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

from pathlib import Path

from cffi import FFI

ffibuilder = FFI()
ffibuilder.cdef(
    """
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

typedef int l_ok; /*!< return type 0 if OK, 1 on error */

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

/*! Array of pix */
struct Pixa
{
    l_int32             n;          /*!< number of Pix in ptr array        */
    l_int32             nalloc;     /*!< number of Pix ptrs allocated      */
    l_uint32            refcount;   /*!< reference count (1 if no clones)  */
    struct Pix        **pix;        /*!< the array of ptrs to pix          */
    struct Boxa        *boxa;       /*!< array of boxes                    */
};
typedef struct Pixa PIXA;

/*! Array of compressed pix */
struct PixaComp
{
    l_int32              n;         /*!< number of PixComp in ptr array    */
    l_int32              nalloc;    /*!< number of PixComp ptrs allocated  */
    l_int32              offset;    /*!< indexing offset into ptr array    */
    struct PixComp     **pixc;      /*!< the array of ptrs to PixComp      */
    struct Boxa         *boxa;      /*!< array of boxes                    */
};
typedef struct PixaComp PIXAC;

struct Box
{
    l_int32            x;
    l_int32            y;
    l_int32            w;
    l_int32            h;
    l_uint32           refcount;      /* reference count (1 if no clones)  */

};
typedef struct Box    BOX;

/*! Array of Box */
struct Boxa
{
    l_int32            n;           /*!< number of box in ptr array        */
    l_int32            nalloc;      /*!< number of box ptrs allocated      */
    l_uint32           refcount;    /*!< reference count (1 if no clones)  */
    struct Box       **box;         /*!< box ptr array                     */
};
typedef struct Boxa BOXA;

/*! String array: an array of C strings */
struct Sarray
{
    l_int32          nalloc;    /*!< size of allocated ptr array         */
    l_int32          n;         /*!< number of strings allocated         */
    l_int32          refcount;  /*!< reference count (1 if no clones)    */
    char           **array;     /*!< string array                        */
};
typedef struct Sarray SARRAY;

/*! Pdf formatted encoding types */
enum {
    L_DEFAULT_ENCODE  = 0,  /*!< use default encoding based on image        */
    L_JPEG_ENCODE     = 1,  /*!< use dct encoding: 8 and 32 bpp, no cmap    */
    L_G4_ENCODE       = 2,  /*!< use ccitt g4 fax encoding: 1 bpp           */
    L_FLATE_ENCODE    = 3,  /*!< use flate encoding: any depth, cmap ok     */
    L_JP2K_ENCODE     = 4   /*!< use jp2k encoding: 8 and 32 bpp, no cmap   */
};

/*! Compressed image data */
struct L_Compressed_Data
{
    l_int32            type;         /*!< encoding type: L_JPEG_ENCODE, etc   */
    l_uint8           *datacomp;     /*!< gzipped raster data                 */
    size_t             nbytescomp;   /*!< number of compressed bytes          */
    char              *data85;       /*!< ascii85-encoded gzipped raster data */
    size_t             nbytes85;     /*!< number of ascii85 encoded bytes     */
    char              *cmapdata85;   /*!< ascii85-encoded uncompressed cmap   */
    char              *cmapdatahex;  /*!< hex pdf array for the cmap          */
    l_int32            ncolors;      /*!< number of colors in cmap            */
    l_int32            w;            /*!< image width                         */
    l_int32            h;            /*!< image height                        */
    l_int32            bps;          /*!< bits/sample; typ. 1, 2, 4 or 8      */
    l_int32            spp;          /*!< samples/pixel; typ. 1 or 3          */
    l_int32            minisblack;   /*!< tiff g4 photometry                  */
    l_int32            predictor;    /*!< flate data has PNG predictors       */
    size_t             nbytes;       /*!< number of uncompressed raster bytes */
    l_int32            res;          /*!< resolution (ppi)                    */
};
typedef struct L_Compressed_Data L_COMP_DATA;

/*! Selection */
struct Sel
{
    l_int32       sy;        /*!< sel height                               */
    l_int32       sx;        /*!< sel width                                */
    l_int32       cy;        /*!< y location of sel origin                 */
    l_int32       cx;        /*!< x location of sel origin                 */
    l_int32     **data;      /*!< {0,1,2}; data[i][j] in [row][col] order  */
    char         *name;      /*!< used to find sel by name                 */
};
typedef struct Sel SEL;

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

/*! Flags for method of extracting barcode widths */
enum {
    L_USE_WIDTHS = 1,     /*!< use histogram of barcode widths           */
    L_USE_WINDOWS = 2     /*!< find best window for decoding transitions */
};

/*! Flags for barcode formats */
enum {
    L_BF_UNKNOWN = 0,     /*!< unknown format                            */
    L_BF_ANY = 1,         /*!< try decoding with all known formats       */
    L_BF_CODE128 = 2,     /*!< decode with Code128 format                */
    L_BF_EAN8 = 3,        /*!< decode with EAN8 format                   */
    L_BF_EAN13 = 4,       /*!< decode with EAN13 format                  */
    L_BF_CODE2OF5 = 5,    /*!< decode with Code 2 of 5 format            */
    L_BF_CODEI2OF5 = 6,   /*!< decode with Interleaved 2 of 5 format     */
    L_BF_CODE39 = 7,      /*!< decode with Code39 format                 */
    L_BF_CODE93 = 8,      /*!< decode with Code93 format                 */
    L_BF_CODABAR = 9,     /*!< decode with Code93 format                 */
    L_BF_UPCA = 10        /*!< decode with UPC A format                  */
};

enum {
    L_SEVERITY_EXTERNAL = 0,   /* Get the severity from the environment   */
    L_SEVERITY_ALL      = 1,   /* Lowest severity: print all messages     */
    L_SEVERITY_DEBUG    = 2,   /* Print debugging and higher messages     */
    L_SEVERITY_INFO     = 3,   /* Print informational and higher messages */
    L_SEVERITY_WARNING  = 4,   /* Print warning and higher messages       */
    L_SEVERITY_ERROR    = 5,   /* Print error and higher messages         */
    L_SEVERITY_NONE     = 6    /* Highest severity: print no messages     */
};

enum {
    SEL_DONT_CARE  = 0,
    SEL_HIT        = 1,
    SEL_MISS       = 2
};

"""
)

ffibuilder.cdef(
    """
PIX * pixRead ( const char *filename );
PIX * pixReadMem ( const l_uint8 *data, size_t size );
PIX * pixReadStream ( FILE *fp, l_int32 hint );
PIX * pixScale ( PIX *pixs, l_float32 scalex, l_float32 scaley );
l_int32 pixFindSkew ( PIX *pixs, l_float32 *pangle, l_float32 *pconf );
l_int32 pixWriteImpliedFormat ( const char *filename, PIX *pix, l_int32 quality, l_int32 progressive );
l_int32 getImpliedFileFormat ( const char *filename );
l_ok pixWriteStream ( FILE *fp, PIX *pix, l_int32 format );
l_ok pixWriteStreamJpeg ( FILE *fp, PIX *pixs, l_int32 quality, l_int32 progressive );
l_ok pixWriteMem ( l_uint8 **pdata, size_t *psize, PIX *pix, l_int32 format );
l_ok pixWriteMemJpeg ( l_uint8 **pdata, size_t *psize, PIX *pix, l_int32 quality, l_int32 progressive );
l_int32
pixWriteMemPng(l_uint8  **pdata,
               size_t    *psize,
               PIX       *pix,
               l_float32  gamma);

void pixDestroy ( PIX **ppix );

l_ok
pixEqual(PIX      *pix1,
         PIX      *pix2,
         l_int32 *psame);

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

PIX * pixConvertTo8(PIX     *pixs, l_int32  cmapflag);

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
pixMaskedThreshOnBackgroundNorm(PIX       *pixs,
                                PIX       *pixim,
                                l_int32    sx,
                                l_int32    sy,
                                l_int32    thresh,
                                l_int32    mincount,
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
pixFindPageForeground ( PIX *pixs,
                        l_int32 threshold,
                        l_int32 mindist,
                        l_int32 erasedist,
                        l_int32 showmorph,
                        PIXAC *pixac );

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

l_int32
pixGenerateCIData(PIX           *pixs,
                  l_int32        type,
                  l_int32        quality,
                  l_int32        ascii85,
                  L_COMP_DATA **pcid);

SARRAY *
pixProcessBarcodes(PIX      *pixs,
                   l_int32   format,
                   l_int32   method,
                   SARRAY  **psaw,
                   l_int32 debugflag);

PIX *
pixaGetPix(PIXA    *pixa,
           l_int32  index,
           l_int32 accesstype);

BOX*
pixaGetBox 	(PIXA *  	pixa,
		    l_int32  	index,
		    l_int32  	accesstype );

PIXA *
pixExtractBarcodes(PIX     *pixs,
                   l_int32 debugflag);

BOXA *
pixLocateBarcodes ( PIX *pixs,
 l_int32 thresh,
 PIX **ppixb,
 PIX **ppixm );

SARRAY *
pixReadBarcodes(PIXA     *pixa,
                l_int32   format,
                l_int32   method,
                SARRAY  **psaw,
                l_int32 debugflag);

PIX *
pixGenHalftoneMask(PIX      *pixs,
                        PIX     **ppixtext,
                        l_int32  *phtfound,
                        PIXA     *pixadb);

l_int32
l_generateCIDataForPdf(const char *fname,
                       PIX *pix,
                       l_int32 quality,
                       L_COMP_DATA **pcid);


BOX *
boxClone ( BOX *box );

BOX *
boxaGetBox ( BOXA *boxa, l_int32 index, l_int32 accessflag );

SEL *
selCreateFromString ( const char *text, l_int32 h, l_int32 w, const char *name );

SEL *
selCreateBrick ( l_int32 h, l_int32 w, l_int32 cy, l_int32 cx, l_int32 type );

char *
selPrintToString(SEL  *sel);

PIX *
pixDilate ( PIX *pixd, PIX *pixs, SEL *sel );

PIX *
pixErode ( PIX *pixd, PIX *pixs, SEL *sel );

PIX *
pixHMT ( PIX *pixd, PIX *pixs, SEL *sel );

PIX *
pixSubtract ( PIX *pixd, PIX *pixs1, PIX *pixs2 );

void
boxDestroy(BOX  **pbox);

void
boxaDestroy ( BOXA **pboxa );

void
pixaDestroy(PIXA **ppixa);

l_ok
pixRenderBoxa ( PIX *pix, BOXA *boxa, l_int32 width, l_int32 op );

void
l_CIDataDestroy(L_COMP_DATA **pcid);

void
sarrayDestroy(SARRAY  **psa);

void
lept_free(void *ptr);

void selDestroy ( SEL **psel );

l_int32
setMsgSeverity(l_int32 newsev);

"""
)


ffibuilder.set_source("ocrmypdf.lib._leptonica", None)

if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
    if Path('ocrmypdf/lib/_leptonica.py').exists() and Path('src/ocrmypdf').exists():
        output = Path('ocrmypdf/lib/_leptonica.py')
        output.rename('src/ocrmypdf/lib/_leptonica.py')
        Path('ocrmypdf/lib').rmdir()
        Path('ocrmypdf').rmdir()
