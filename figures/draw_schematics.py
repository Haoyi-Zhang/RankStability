"""Draw the manuscript schematics directly as font-embedded vector PDFs.

Run: python figures/draw_schematics.py --output figures
Requires Python 3.9+ and Matplotlib. No TeX engine or network is used.
The diagrams express the defined model; they are not measurement plots.
"""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

plt.rcParams.update({'font.family':'STIXGeneral', 'mathtext.fontset':'stix',
                     'font.size':9, 'pdf.fonttype':42, 'ps.fonttype':42,
                     'text.usetex':False, 'axes.unicode_minus':False})
CM = 1 / 2.54

class Drawing:
    def __init__(self, bounds):
        x0,y0,x1,y1 = bounds
        self.fig = plt.figure(figsize=((x1-x0)*CM,(y1-y0)*CM))
        self.ax = self.fig.add_axes([0,0,1,1], xlim=(x0,x1), ylim=(y0,y1))
        self.ax.set_aspect('equal'); self.ax.axis('off')
        self.nodes = {}
        self.labels = []

    def text(self,x,y,label,size=9,ha='center',va='center'):
        artist=self.ax.text(x,y,label,fontsize=size,ha=ha,va=va,
                            linespacing=1.15,clip_on=False,zorder=4)
        self.labels.append([artist,None])
        return artist

    def box(self,name,x,y,w,h,label,dashed=False,shape='rect',size=9):
        style = {'edgecolor':'black','facecolor':'white','linewidth':.55,
                 'linestyle':(0,(4,3)) if dashed else 'solid', 'zorder':2}
        if shape == 'diamond':
            obj = Polygon([(x-w/2,y),(x,y+h/2),(x+w/2,y),(x,y-h/2)],**style)
        elif shape == 'circle': obj = Circle((x,y),w/2,**style)
        else: obj = Rectangle((x-w/2,y-h/2),w,h,**style)
        self.ax.add_patch(obj); self.text(x,y,label,size)
        self.labels[-1][1]=(x-w/2,y-h/2,x+w/2,y+h/2)
        self.nodes[name] = (x,y,w,h,shape)

    def point(self,name,side):
        x,y,w,h,_ = self.nodes[name]
        return {'n':(x,y+h/2),'s':(x,y-h/2),'e':(x+w/2,y),
                'w':(x-w/2,y),'nw':(x-w/2,y+h/2),
                'ne':(x+w/2,y+h/2),'c':(x,y)}[side]

    def line(self,points,dashed=False):
        xs,ys=zip(*points)
        self.ax.plot(xs,ys,color='black',linewidth=.55,
                     linestyle=(0,(4,3)) if dashed else 'solid',zorder=1)

    def arrow(self,p,q,dashed=False,via=()):
        points=[p,*via,q]
        if via:self.line(points[:-1],dashed)
        self.ax.add_patch(FancyArrowPatch(points[-2],points[-1],
                         arrowstyle='-|>',mutation_scale=7.5,linewidth=.55,
                         color='black',shrinkA=0,shrinkB=0,
                         linestyle=(0,(4,3)) if dashed else 'solid',zorder=1))

    def edge(self,a,b,sa='s',sb='n',**kwargs):
        self.arrow(self.point(a,sa),self.point(b,sb),**kwargs)

    def frame(self,x,y,w,h):
        self.ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor='black',
                                   linewidth=.55,linestyle=(0,(4,3)),zorder=0))

    def save(self,out,name):
        # Fixed physical canvas: do not enlarge or rasterize the scientific figure.
        self.fig.canvas.draw()
        renderer=self.fig.canvas.get_renderer()
        x0,x1=self.ax.get_xlim();y0,y1=self.ax.get_ylim()
        for artist,node in self.labels:
            b=artist.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            if b.x0<x0-.02 or b.x1>x1+.02 or b.y0<y0-.02 or b.y1>y1+.02:
                raise ValueError(name+': clipped label '+repr(artist.get_text()))
            if node and (b.x0<node[0]-.02 or b.x1>node[2]+.02 or b.y0<node[1]-.02 or b.y1>node[3]+.02):
                raise ValueError(name+': label exceeds node '+repr(artist.get_text()))
        self.fig.savefig(out/(name+'.pdf'),format='pdf',
                         metadata={'Creator':'Python Matplotlib','Producer':None,
                                   'CreationDate':None,'ModDate':None})
        plt.close(self.fig)



import math

def segment(d,start,end,radius=.3,dashed=False,arrow=False):
    dx=end[0]-start[0];dy=end[1]-start[1];length=math.hypot(dx,dy)
    ux=dx/length;uy=dy/length
    p=(start[0]+radius*ux,start[1]+radius*uy)
    q=(end[0]-radius*ux,end[1]-radius*uy)
    if arrow:d.arrow(p,q,dashed=dashed)
    else:d.line([p,q],dashed=dashed)

def draw(out):
    # Each edge denotes an individual mutant. The two perfect matchings are distinct samples.
    d=Drawing((-.55,-.7,5.05,2.3))
    pos={'a0':(0,1.6),'a1':(0,0),'b0':(4.5,1.6),'b1':(4.5,0)}
    segment(d,pos['a0'],pos['b0']);segment(d,pos['a1'],pos['b1'])
    segment(d,pos['a0'],pos['b1'],dashed=True);segment(d,pos['a1'],pos['b0'],dashed=True)
    for key,label in [('a0',r'$A_0$'),('a1',r'$A_1$'),('b0',r'$B_0$'),('b1',r'$B_1$')]:
        d.box(key,*pos[key],.6,.6,label,shape='circle',size=8.5)
    d.text(2.25,1.9,r'$0:\ A,\ 1$',size=8.5)
    d.text(2.25,-.32,r'$1:\ B,\ 1/2$',size=8.5)
    for x,label in [(.95,r'$2:\ A,\ 1/3$'),(3.55,r'$3:\ B,\ 1/4$')]:
        text=d.text(x,1.04,label,size=8.5)
        text.set_bbox({'facecolor':'white','edgecolor':'none','pad':1})
    d.save(out,'crossing')

    # Directed lower-bound circulation, including the cardinality return arc t0 -> s0.
    d=Drawing((-.5,-2.15,6.1,1.65))
    pos={'s':(0,0),'a0':(1.6,.7),'a1':(1.6,-.7),
         'b0':(4,.7),'b1':(4,-.7),'t':(5.6,0)}
    for x,y in [('s','a0'),('s','a1'),('a0','b0'),('a0','b1'),
                ('a1','b0'),('a1','b1'),('b0','t'),('b1','t')]:segment(d,pos[x],pos[y],arrow=True)
    d.arrow((5.6,-.3),(0,-.3),via=((5.6,-1.5),(0,-1.5)))
    for key,label in [('s',r'$s_0$'),('a0',r'$A_0$'),('a1',r'$A_1$'),
                      ('b0',r'$B_0$'),('b1',r'$B_1$'),('t',r'$t_0$')]:
        d.box(key,*pos[key],.6,.6,label,shape='circle',size=8.5)
    for x,label in [(.8,'A quotas'),(2.8,'mutant arcs'),(4.8,'B quotas')]:d.text(x,1.25,label,size=8.5)
    d.text(2.8,-1.83,r'$[L,\min(U,u)]$',size=8.5)
    d.save(out,'network')

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path(__file__).resolve().parent)
    output=parser.parse_args().output
    output.mkdir(parents=True,exist_ok=True)
    draw(output)
