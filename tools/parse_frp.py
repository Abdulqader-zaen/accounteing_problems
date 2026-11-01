import struct,sys
def cells(path):
    d=open(path,'rb').read(); M=b'\xff\xff\xff\x00\x01\x00'; p=0; out=[]
    while True:
        p=d.find(M,p)
        if p<0: break
        n=struct.unpack('<H',d[p+6:p+8])[0]
        t=d[p+8:p+8+n].decode('cp1256','replace')
        x,y,w,h=struct.unpack('<iiii',d[p-30:p-14]) if p>=30 else (0,0,0,0)
        out.append((x,y,t)); p+=8
    return out
if __name__=='__main__':
    for c in cells(sys.argv[1])[:int(sys.argv[2])]: print(c)
