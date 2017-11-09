"""
Python script to create a example of storing an adaptive mesh in NeXus.

Here is the resulting NeXus file:

amr_example:NXroot
  @HDF5_Version = '1.8.18'
  @file_name = '/Users/rosborn/Desktop/amr_example.nxs'
  @file_time = '2017-11-09T15:39:43.139972'
  @h5py_version = '2.7.0'
  @nexusformat_version = '0.4.12+5.g26d6c0e'
  entry:NXentry
    data:NXdata
      @axes = ['Qk' 'Qh']
      @signal = 'SQ'
      Qh = float32(17)
      Qk = float32(17)
      SQ = float32(17x17)
      subdata1:NXdata
        @axes = ['Qk' 'Qh']
        @origin = [4 4]
        @signal = 'SQ'
        Qh = float32(5)
        Qk = float32(5)
        SQ = float32(5x5)
      subdata2:NXdata
        @axes = ['Qk' 'Qh']
        @origin = [12  4]
        @signal = 'SQ'
        Qh = float32(5)
        Qk = float32(5)
        SQ = float32(5x5)
      subdata3:NXdata
        @axes = ['Qk' 'Qh']
        @origin = [12 12]
        @signal = 'SQ'
        Qh = float32(5)
        Qk = float32(5)
        SQ = float32(5x5)
      subdata4:NXdata
        @axes = ['Qk' 'Qh']
        @origin = [ 4 12]
        @signal = 'SQ'
        Qh = float32(5)
        Qk = float32(5)
        SQ = float32(5x5)

Each subdata group is a valid NXdata group, which have x and y axis values
that are aligned to their position in the parent NXdata group. The script 
generating the composite plot (parent + children) uses the 'origin' attribute
of each subdata group to align it to the correct position.
"""
def gauss(x, y, integral=2.0, sigma=0.05):
    return integral * np.exp(-(x**2+y**2)/(2*np.pi*sigma**2))


x = NXfield(np.linspace(-2,2,17), name='Qh', dtype=np.float32)
y = NXfield(np.linspace(-2,2,17), name='Qk', dtype=np.float32)
X,Y = np.meshgrid(x,y)
z = NXfield(np.abs(np.sin(0.5*X*np.pi)*np.sin(0.5*Y*np.pi)), name='SQ', 
            dtype=np.float32)
z[4,4] = z[4,12]= z[12,4] = z[12,12] = 3.0

entry=NXentry()
entry.data=NXdata(z,(y,x))

xx=NXfield(np.linspace(-0.1,0.1,5), name='Qh', dtype=np.float32)
yy=NXfield(np.linspace(-0.1,0.1,5), name='Qk', dtype=np.float32)
XX,YY=np.meshgrid(xx,yy)
zz=NXfield(gauss(XX,YY)+1, name='SQ', dtype=np.float32)

entry.plot()

xb, yb = x.boundaries().nxdata, y.boundaries().nxdata

def get_extent(i, j):
    global xb, yb
    return xb[i], xb[i+1], yb[j], yb[j+1]

def subdata(i, j):
    global xx, yy, zz
    origin = [i, j]
    data = NXdata(zz, (yy+y[j], xx+x[i]))
    data.attrs['origin'] = [i, j]
    subplot(data)
    return data

def subplot(data):
    plotview.ax.imshow(data.nxsignal.nxdata, 
                       extent=get_extent(*data.attrs['origin']), 
                       norm=plotview.norm)
    plotview.draw()

entry.data.subdata1 = subdata(4, 4)
entry.data.subdata2 = subdata(12, 4)
entry.data.subdata3 = subdata(12 ,12)
entry.data.subdata4 = subdata(4 ,12)

amr_example = NXroot(entry)
