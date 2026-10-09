"""PyTorch reproduction of the Growing NCA baseline, with portable browser weights."""
import argparse, json, random, time
from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image, ImageDraw

class NCA(nn.Module):
    def __init__(self, channels=16, hidden=128, fire_rate=.5):
        super().__init__(); self.channels,self.hidden,self.fire_rate=channels,hidden,fire_rate
        self.fc1=nn.Conv2d(channels*3,hidden,1); self.fc2=nn.Conv2d(hidden,channels,1); nn.init.zeros_(self.fc2.weight); nn.init.zeros_(self.fc2.bias)
        self.register_buffer('sobel_x',torch.tensor([[-1,0,1],[-2,0,2],[-1,0,1]],dtype=torch.float32).view(1,1,3,3)/8)
    def forward(self,x,fire_rate=None):
        pre_alive=F.max_pool2d(x[:,3:4],3,1,1)>.1
        c=x.shape[1]; kx=self.sobel_x.repeat(c,1,1,1); ky=kx.transpose(2,3)
        perceive=torch.cat([x,F.conv2d(x,kx,padding=1,groups=c),F.conv2d(x,ky,padding=1,groups=c)],1)
        delta=self.fc2(F.relu(self.fc1(perceive))); rate=self.fire_rate if fire_rate is None else fire_rate
        x=x+delta*(torch.rand_like(x[:,:1])<=rate)
        post_alive=F.max_pool2d(x[:,3:4],3,1,1)>.1
        return x*(pre_alive & post_alive)
    def seed(self,n,size,device):
        x=torch.zeros(n,self.channels,size,size,device=device); x[:,:,size//2,size//2]=1; x[:,:3,size//2,size//2]=0; return x

def image_tensor(path, device):
    im=Image.open(path).convert('RGBA'); a=torch.from_numpy(__import__('numpy').asarray(im).copy()).float().permute(2,0,1)/255
    a[:3] *= a[3:4]
    return a.unsqueeze(0).to(device)
def edge_loss(image, target):
    channels=image.shape[1]; sx=torch.tensor([[-1,0,1],[-2,0,2],[-1,0,1]],dtype=image.dtype,device=image.device).view(1,1,3,3)/8; sx=sx.repeat(channels,1,1,1); sy=sx.transpose(2,3)
    return F.mse_loss(F.conv2d(image,sx,padding=1,groups=channels),F.conv2d(target,sx,padding=1,groups=channels))+F.mse_loss(F.conv2d(image,sy,padding=1,groups=channels),F.conv2d(target,sy,padding=1,groups=channels))
def export(model,path,size,name):
    d={'format':'automata-studio-nca-v1','name':name,'size':size,'channels':model.channels,'hidden':model.hidden,'fireRate':model.fire_rate,'weights':{'w1':model.fc1.weight.detach().cpu().reshape(-1).tolist(),'b1':model.fc1.bias.detach().cpu().tolist(),'w2':model.fc2.weight.detach().cpu().reshape(-1).tolist(),'b2':model.fc2.bias.detach().cpu().tolist()}}
    path.write_text(json.dumps(d,separators=(',',':')))
def sheet(model,target,path,device,steps=(0,16,32,64,96,128)):
    x=model.seed(1,target.shape[-1],device); frames=[]
    with torch.no_grad():
        for t in range(max(steps)+1):
            if t in steps: frames.append((x[0,:4].clamp(0,1).permute(1,2,0).cpu().numpy()*255).astype('uint8'))
            x=model(x)
    tile=target.shape[-1]; out=Image.new('RGBA',((len(frames)+1)*tile,tile)); out.paste(Image.fromarray((target[0].permute(1,2,0).cpu().numpy()*255).astype('uint8')),(0,0))
    for i,f in enumerate(frames):out.paste(Image.fromarray(f),(tile*(i+1),0))
    out.save(path)
def main():
    p=argparse.ArgumentParser();p.add_argument('--target',required=True);p.add_argument('--run',required=True);p.add_argument('--steps',type=int,default=3000);p.add_argument('--batch',type=int,default=8);p.add_argument('--pool',type=int,default=256);p.add_argument('--padding',type=int,default=8);p.add_argument('--mode',choices=('grow','persistent'),default='grow');p.add_argument('--edge-weight',type=float,default=0);p.add_argument('--min-rollout',type=int,default=64);p.add_argument('--max-rollout',type=int,default=96);p.add_argument('--learning-rate',type=float,default=2e-3);p.add_argument('--lr-decay',type=float,default=2000);p.add_argument('--resume');p.add_argument('--seed',type=int,default=1);a=p.parse_args()
    random.seed(a.seed);torch.manual_seed(a.seed); device=torch.device('mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu')
    target=image_tensor(a.target,device); assert target.shape[-2:]==(64,64),'target must be 64x64'; target=F.pad(target,(a.padding,a.padding,a.padding,a.padding)); size=target.shape[-1]
    run=Path('nca-runs')/a.run;run.mkdir(parents=True,exist_ok=True); (run/'target.png').write_bytes(Path(a.target).read_bytes())
    model=NCA().to(device);opt=torch.optim.Adam(model.parameters(),a.learning_rate);pool=model.seed(a.pool,size,device).detach();start=0
    if a.resume:
        d=torch.load(a.resume,map_location=device,weights_only=False); config=d.get('config',{}); model=NCA(config.get('channels',16),config.get('hidden',128)).to(device);model.load_state_dict(d['model']);opt=torch.optim.Adam(model.parameters(),a.learning_rate);opt.load_state_dict(d['opt']);pool=d.get('pool',pool.cpu()).to(device);start=d['step']+1
    log=(run/'progress.jsonl').open('a'); started=time.time()
    for step in range(start,a.steps):
        ids=torch.randperm(a.pool,device=device)[:a.batch]
        if a.mode=='grow': x=model.seed(a.batch,size,device)
        else:
            x=pool[ids].clone(); losses=((x[:,:4]-target)**2).mean((1,2,3)); x=x[torch.argsort(losses,descending=True)]; x[0]=model.seed(1,size,device)[0]
        learning_rate=a.learning_rate*10**(-step/a.lr_decay)
        for group in opt.param_groups: group['lr']=learning_rate
        for _ in range(random.randint(a.min_rollout,a.max_rollout)): x=model(x)
        shown=x[:,:4]; expanded=target.expand_as(shown); pixel=F.mse_loss(shown,expanded); edges=edge_loss(shown,expanded) if a.edge_weight else shown.new_tensor(0); loss=pixel+a.edge_weight*edges;opt.zero_grad();loss.backward()
        for q in model.parameters():
            if q.grad is not None:q.grad.div_(q.grad.norm()+1e-8)
        opt.step()
        if a.mode=='persistent': pool[ids]=x.detach()
        if step%100==0 or step==a.steps-1:
            record={'step':step,'loss':float(loss),'pixel_loss':float(pixel),'edge_loss':float(edges),'learning_rate':learning_rate,'seconds':round(time.time()-started,1),'device':str(device),'mode':a.mode};print(json.dumps(record),flush=True);log.write(json.dumps(record)+'\n');log.flush();sheet(model,target,run/f'growth-{step:05}.png',device);state={'model':model.state_dict(),'opt':opt.state_dict(),'pool':pool.cpu(),'step':step,'config':{'channels':model.channels,'hidden':model.hidden,'mode':a.mode}};torch.save(state,run/'checkpoint.pt');
            if step%500==0 or step==a.steps-1: torch.save(state,run/f'checkpoint-{step:05}.pt')
            export(model,run/'model.json',size,a.run)
    log.close()
if __name__=='__main__':main()
