import struct,glob,sys,json
import numpy as np
from PIL import Image
def load(dirn):
    P=glob.glob(dirn+'/ppu_*.vram.bin')[0]
    v=open(P,'rb').read()
    scr=np.array(Image.open(dirn+'/final.png').convert('RGB')).astype(np.int32)
    return v,scr
def bgimg(v,mb,cb=0x8000):
    img=np.zeros((256,256),np.int32)
    for cy in range(32):
        for cx in range(32):
            e=struct.unpack_from('<H',v,mb+2*(cy*32+cx))[0]; n,hf,vf,pl=e&0x3FF,(e>>10)&1,(e>>11)&1,e>>12
            t=np.frombuffer(v[cb+n*32:cb+n*32+32],np.uint8)
            px=np.zeros(64,np.int32); px[0::2]=t&15; px[1::2]=t>>4; px=px.reshape(8,8)
            if hf: px=px[:,::-1]
            if vf: px=px[::-1,:]
            img[cy*8:cy*8+8,cx*8:cx*8+8]=np.where(px>0,pl*16+px,0)
    return img
def scroll(v,scr,mb):
    key=scr[:,:,0]*65536+scr[:,:,1]*256+scr[:,:,2]; sh=(key[:,1:]==key[:,:-1])
    img=bgimg(v,mb); big=np.tile(img,(2,2)); best=(0,0,0)
    for sy in range(0,256,1):
        for sx in range(0,256,1):
            w=big[sy:sy+160,sx:sx+240]; m=(w[:,1:]>0)&(w[:,:-1]>0)
            if m.sum()<500: continue
            sc=(((w[:,1:]==w[:,:-1])==sh)&m).sum()/m.sum()
            if sc>best[0]: best=(sc,sx,sy)
    return best
if __name__=='__main__':
    for d in sys.argv[1:]:
        v,scr=load(d); print(d, scroll(v,scr,0x1000))
