"""Evaluate a checkpoint over fresh stochastic seeds and save contact sheets."""
import argparse, json
from pathlib import Path
import torch
import torch.nn.functional as F
from PIL import Image
from train import NCA, image_tensor

def frame(state):
    rgba=state[0,:4].clamp(0,1).permute(1,2,0).cpu().numpy()
    alpha=rgba[...,3:4]; rgba[...,:3]=__import__('numpy').where(alpha>.001,rgba[...,:3]/__import__('numpy').maximum(alpha,.001),0)
    return Image.fromarray((rgba*255).clip(0,255).astype('uint8'),'RGBA')

def main():
    p=argparse.ArgumentParser();p.add_argument('--target',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--run',required=True);p.add_argument('--seeds',default='7,19,41');p.add_argument('--steps',default='0,32,64,96,128,160,256');a=p.parse_args()
    device=torch.device('mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu');d=torch.load(a.checkpoint,map_location=device,weights_only=False);cfg=d.get('config',{});model=NCA(cfg.get('channels',16),cfg.get('hidden',128)).to(device);model.load_state_dict(d['model']);model.eval();target=image_tensor(a.target,device);size=target.shape[-1];steps=[int(v) for v in a.steps.split(',')];results=[];out=Path(a.run);out.mkdir(parents=True,exist_ok=True)
    for seed in [int(v) for v in a.seeds.split(',')]:
        torch.manual_seed(seed);state=model.seed(1,size,device);images=[];losses={}
        with torch.no_grad():
            for step in range(max(steps)+1):
                if step in steps:
                    image=frame(state);images.append(image);image.save(out/f'rollout-seed-{seed}-step-{step:03}.png');losses[str(step)]=float(F.mse_loss(state[:,:4],target))
                state=model(state)
        sheet=Image.new('RGBA',(size*len(images),size));
        for i,image in enumerate(images):sheet.paste(image,(size*i,0),image)
        sheet.save(out/f'evaluation-seed-{seed}.png');results.append({'seed':seed,'loss_by_step':losses})
    (out/'evaluation.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
if __name__=='__main__':main()
