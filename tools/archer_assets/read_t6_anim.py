"""Decode OAT's compiled T6 animation interchange (v19), without game memory.

Format reference: OpenAssetTools v0.33.0 CompiledXAnimLoader.cpp (GPL-3.0),
retained under tmp/archer_assets/oat_source. This reader exposes source keys;
Blender resolves/retargets the skeleton and exports BO3 animation binaries.
"""
import io, math, struct
from pathlib import Path


def read(path):
    stream=io.BytesIO(Path(path).read_bytes())
    def unpack(fmt):
        size=struct.calcsize('<'+fmt);data=stream.read(size)
        if len(data)!=size:raise ValueError(f'Truncated animation at {stream.tell()}: {path}')
        out=struct.unpack('<'+fmt,data);return out[0] if len(out)==1 else out
    def string():
        out=bytearray()
        while True:
            b=stream.read(1)
            if not b:raise ValueError('Unterminated bone/note name')
            if b==b'\0':return out.decode('utf-8')
            out.extend(b)
    version,nframes,nbones,flags,kind,fps=unpack('HHHBBH')
    assert version==19 and fps>0 and nbones>0,(version,fps,nbones)
    assert not flags&2 and not (flags&128 and flags&4),'Delta track not a viewmodel clip'
    assert not (flags&8 and not flags&128),'Streamable T5 is not supported'
    count=nframes+1 if flags&1 else nframes
    bits=(nbones+7)//8;flip=stream.read(bits);half=stream.read(bits)
    names=[string() for _ in range(nbones)]
    def indices(n):
        if n==1:return [0]
        if n>=count:return list(range(n))
        return [unpack('B' if count-1<256 else 'H') for _ in range(n)]
    tracks={}
    for index,name in enumerate(names):
        nq=unpack('H');qi=indices(nq);quats=[]
        for i in range(nq):
            h=bool(half[index//8]&(1<<(index%8)))
            v=[0,0,unpack('h')] if h else list(unpack('3h'))
            w=math.floor(math.sqrt(max(0,32767**2-sum(x*x for x in v)))+.5)
            q=[x/32767 for x in [*v,w]]
            negative=(i==0 and bool(flip[index//8]&(1<<(index%8)))) or (i>0 and sum(a*b for a,b in zip(quats[-1][1],q))<0)
            if negative:q=[-x for x in q]
            quats.append((qi[i],q))
        nt=unpack('H');ti=indices(nt);pos=[]
        if nt==1:pos=[(0,unpack('3f'))]
        elif nt>1:
            small=unpack('B');lo=unpack('3f');span=unpack('3f');scale=0.003921568859368563 if small else 0.00001525902189314365
            for i in range(nt):
                v=unpack('3B' if small else '3H')
                pos.append((ti[i],[lo[j]+v[j]*span[j]*scale for j in range(3)]))
        tracks[name]={'pos':pos,'rot':quats}
    notes=[]
    for _ in range(unpack('B')):
        name=string();notes.append({'name':name,'frame':unpack('H')})
    assert not stream.read(1),f'Unconsumed animation bytes: {path}'
    return {'source':str(path),'frames':count,'fps':fps,'loop':bool(flags&1),'kind':kind,'tracks':tracks,'notes':notes}


if __name__=='__main__':
    import sys,json
    for path in sys.argv[1:]:
        a=read(path);print(json.dumps({k:(len(v) if k=='tracks' else v) for k,v in a.items()}))
