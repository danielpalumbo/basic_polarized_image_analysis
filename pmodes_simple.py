import h5py
import numpy as np
import ehtim as eh

def pmodes(im, ms, r_min=0, r_max=1e3, norm_in_int = False, norm_with_StokesI = True):
  """Return beta_m coefficients for m in ms within extent r_min/r_max."""

  if type(im) == eh.image.Image:
    npix = im.xdim
    iarr = im.ivec.reshape(npix, npix)
    qarr = im.qvec.reshape(npix, npix)
    uarr = im.uvec.reshape(npix, npix)
    varr = im.vvec.reshape(npix, npix)
    fov_muas = im.fovx()/eh.RADPERUAS

  else:
    hfp = h5py.File(im,'r')
    DX = hfp['header']['camera']['dx'][()]
    dsource = hfp['header']['dsource'][()]
    lunit = hfp['header']['units']['L_unit'][()]
    scale = hfp['header']['scale'][()]
    pol = np.flip(np.copy(hfp['pol']).transpose((1,0,2)),axis=0) * scale
    hfp.close()
    fov_muas = DX / dsource * lunit * 2.06265e11
    npix = pol.shape[0]
    iarr = pol[:,:,0]
    qarr = pol[:,:,1]
    uarr = pol[:,:,2]
    varr = pol[:,:,3]

  parr = qarr + 1j*uarr
  normparr = np.abs(parr)
  marr = parr/iarr
  phatarr = parr/normparr
  area = (r_max*r_max - r_min*r_min) * np.pi
  pxi = (np.arange(npix)-0.01)/npix-0.5
  pxj = np.arange(npix)/npix-0.5
  mui = pxi*fov_muas
  muj = pxj*fov_muas
  MUI,MUJ = np.meshgrid(mui,muj)
  MUDISTS = np.sqrt(np.power(MUI,2.)+np.power(MUJ,2.))

  # get angles measured East of North
  PXI,PXJ = np.meshgrid(pxi,pxj)
  angles = np.arctan2(-PXJ,PXI) - np.pi/2.
  angles[angles<0.] += 2.*np.pi

  # get flux in annulus
  tf = iarr [ (MUDISTS<=r_max) & (MUDISTS>=r_min) ].sum()

  # get total polarized flux in annulus
  pf = normparr [ (MUDISTS<=r_max) & (MUDISTS>=r_min) ].sum()

  #get number of pixels in annulus
  npix = iarr [ (MUDISTS<=r_max) & (MUDISTS>=r_min) ].size

  # compute betas
  betas = []
  for m in ms:
    qbasis = np.cos(-angles*m)
    ubasis = np.sin(-angles*m)
    pbasis = qbasis + 1.j*ubasis
    if norm_in_int:
      if norm_with_StokesI:
        prod = marr * pbasis
      else:
        prod = phatarr * pbasis
      coeff = prod[ (MUDISTS <= r_max) & (MUDISTS >= r_min) ].sum()
      coeff /= npix
    else:
      prod = parr * pbasis
      coeff = prod[ (MUDISTS<=r_max) & (MUDISTS>=r_min) ].sum()
      if norm_with_StokesI:
        coeff /= tf
      else:
        coeff /= pf
    betas.append(coeff)


  return betas
