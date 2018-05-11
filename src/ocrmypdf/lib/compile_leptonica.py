#!/usr/bin/env python3
# © 2017 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

from cffi import FFI

ffibuilder = FFI()
ffibuilder.set_source("ocrmypdf.lib._leptonica", None)
ffibuilder.cdef("""
typedef signed char             l_int8;
typedef unsigned char           l_uint8;
typedef short                   l_int16;
typedef unsigned short          l_uint16;
typedef int                     l_int32;
typedef unsigned int            l_uint32;
typedef float                   l_float32;
typedef double                  l_float64;
typedef long long               l_int64;
typedef unsigned long long      l_uint64;

struct Pix
{
    l_uint32             w;           /* width in pixels                   */
    l_uint32             h;           /* height in pixels                  */
    l_uint32             d;           /* depth in bits (bpp)               */
    l_uint32             spp;         /* number of samples per pixel       */
    l_uint32             wpl;         /* 32-bit words/line                 */
    l_uint32             refcount;    /* reference count (1 if no clones)  */
    l_int32              xres;        /* image res (ppi) in x direction    */
                                      /* (use 0 if unknown)                */
    l_int32              yres;        /* image res (ppi) in y direction    */
                                      /* (use 0 if unknown)                */
    l_int32              informat;    /* input file format, IFF_*          */
    l_int32              special;     /* special instructions for I/O, etc */
    char                *text;        /* text string associated with pix   */
    struct PixColormap  *colormap;    /* colormap (may be null)            */
    l_uint32            *data;        /* the image data                    */
};
typedef struct Pix PIX;

struct PixColormap
{
    void            *array;     /* colormap table (array of RGBA_QUAD)     */
    l_int32          depth;     /* of pix (1, 2, 4 or 8 bpp)               */
    l_int32          nalloc;    /* number of color entries allocated       */
    l_int32          n;         /* number of color entries used            */
};
typedef struct PixColormap  PIXCMAP;

struct Box
{
    l_int32            x;
    l_int32            y;
    l_int32            w;
    l_int32            h;
    l_uint32           refcount;      /* reference count (1 if no clones)  */

};
typedef struct Box    BOX;

enum {
    REMOVE_CMAP_TO_BINARY = 0,     /*!< remove colormap for conv to 1 bpp  */
    REMOVE_CMAP_TO_GRAYSCALE = 1,  /*!< remove colormap for conv to 8 bpp  */
    REMOVE_CMAP_TO_FULL_COLOR = 2, /*!< remove colormap for conv to 32 bpp */
    REMOVE_CMAP_WITH_ALPHA = 3,    /*!< remove colormap and alpha          */
    REMOVE_CMAP_BASED_ON_SRC = 4   /*!< remove depending on src format     */
};

/*! Access and storage flags */
enum {
    L_NOCOPY = 0,     /*!< do not copy the object; do not delete the ptr  */
    L_INSERT = L_NOCOPY,    /*!< stuff it in; do not copy or clone        */
    L_COPY = 1,       /*!< make/use a copy of the object                  */
    L_CLONE = 2,      /*!< make/use clone (ref count) of the object       */
    L_COPY_CLONE = 3  /*!< make a new array object (e.g., pixa) and fill  */
                      /*!< the array with clones (e.g., pix)              */
};

""")

ffibuilder.cdef("""
PIX * pixRead ( const char *filename );
PIX * pixScale ( PIX *pixs, l_float32 scalex, l_float32 scaley );
l_int32 pixFindSkew ( PIX *pixs, l_float32 *pangle, l_float32 *pconf );
l_int32 pixWriteImpliedFormat ( const char *filename, PIX *pix, l_int32 quality, l_int32 progressive );
l_int32
pixWriteMemPng(l_uint8  **pdata,
               size_t    *psize,
               PIX       *pix,
               l_float32  gamma);

void pixDestroy ( PIX **ppix );

PIX *
pixEndianByteSwapNew(PIX  *pixs);

PIX * pixDeskew ( PIX *pixs, l_int32 redsearch );
char * getLeptonicaVersion (  );
l_int32 pixCorrelationBinary(PIX *pix1, PIX *pix2, l_float32 *pval);
PIX *pixRotate180(PIX *pixd, PIX *pixs);
PIX *
pixRotateOrth(PIX     *pixs,
              l_int32  quads);

l_int32 pixCountPixels ( PIX *pix, l_int32 *pcount, l_int32 *tab8 );
PIX * pixAnd ( PIX *pixd, PIX *pixs1, PIX *pixs2 );
l_int32 * makePixelSumTab8 ( void );

PIX * pixDeserializeFromMemory ( const l_uint32 *data, size_t nbytes );
l_int32 pixSerializeToMemory ( PIX *pixs, l_uint32 **pdata, size_t *pnbytes );

PIX * pixConvertRGBToLuminance(PIX *pixs);

PIX * pixRemoveColormap(PIX *pixs, l_int32  type);

l_int32
pixOtsuAdaptiveThreshold(PIX       *pixs,
                         l_int32    sx,
                         l_int32    sy,
                         l_int32    smoothx,
                         l_int32    smoothy,
                         l_float32  scorefract,
                         PIX      **ppixth,
                         PIX      **ppixd);

PIX *
pixOtsuThreshOnBackgroundNorm(PIX       *pixs,
                              PIX       *pixim,
                              l_int32    sx,
                              l_int32    sy,
                              l_int32    thresh,
                              l_int32    mincount,
                              l_int32    bgval,
                              l_int32    smoothx,
                              l_int32    smoothy,
                              l_float32  scorefract,
                              l_int32   *pthresh);

PIX *
pixCleanBackgroundToWhite(PIX       *pixs,
                          PIX       *pixim,
                          PIX       *pixg,
                          l_float32  gamma,
                          l_int32    blackval,
                          l_int32    whiteval);

BOX *
pixFindPageForeground(PIX         *pixs,
                      l_int32      threshold,
                      l_int32      mindist,
                      l_int32      erasedist,
                      l_int32      pagenum,
                      l_int32      showmorph,
                      l_int32      display,
                      const char  *pdfdir);

PIX *
pixClipRectangle(PIX   *pixs,
                 BOX   *box,
                 BOX  **pboxc);

PIX *
pixBackgroundNorm(PIX     *pixs,
                  PIX     *pixim,
                  PIX     *pixg,
                  l_int32  sx,
                  l_int32  sy,
                  l_int32  thresh,
                  l_int32  mincount,
                  l_int32  bgval,
                  l_int32  smoothx,
                  l_int32  smoothy);

PIX *
pixGammaTRC(PIX       *pixd,
            PIX       *pixs,
            l_float32  gamma,
            l_int32    minval,
            l_int32    maxval);


l_int32
pixNumSignificantGrayColors(PIX       *pixs,
                            l_int32    darkthresh,
                            l_int32    lightthresh,
                            l_float32  minfract,
                            l_int32    factor,
                            l_int32   *pncolors);

l_int32
pixColorFraction(PIX        *pixs,
                 l_int32     darkthresh,
                 l_int32     lightthresh,
                 l_int32     diffthresh,
                 l_int32     factor,
                 l_float32  *ppixfract,
                 l_float32  *pcolorfract);

PIX *
pixColorMagnitude(PIX     *pixs,
                  l_int32  rwhite,
                  l_int32  gwhite,
                  l_int32  bwhite,
                  l_int32  type);

PIX *
pixMaskOverColorPixels(PIX     *pixs,
                       l_int32  threshdiff,
                       l_int32  mindist);

l_int32
pixGetAverageMaskedRGB(PIX        *pixs,
                       PIX        *pixm,
                       l_int32     x,
                       l_int32     y,
                       l_int32     factor,
                       l_int32     type,
                       l_float32  *prval,
                       l_float32  *pgval,
                       l_float32  *pbval);

PIX * 
pixGlobalNormRGB(PIX * 	pixd,
                 PIX * 	pixs,
                 l_int32 	rval,
                 l_int32 	gval,
                 l_int32 	bval,
                 l_int32 	mapval); 

PIX *
pixInvert(PIX * pixd,
          PIX * pixs);

PIX *
pixRemoveColormapGeneral(PIX     *pixs,
                         l_int32  type,
                         l_int32  ifnocmap);

void                 
boxDestroy(BOX  **pbox);

void
lept_free(void *ptr);  
""")


if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
