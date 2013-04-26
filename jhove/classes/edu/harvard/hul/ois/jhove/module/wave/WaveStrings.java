/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

/**
 *  A class for holding arrays of informative strings that will go into 
 *  properties of a WAVE object. 
 *
 * @author Gary McGath
 *
 */
public class WaveStrings {

    /** A private constructor just to make sure nobody
       instantiates the class by mistake. */
    private WaveStrings() 
    {
    }


    /** Strings for data compression formats; indexed by
     *  COMPRESSION_INDEX */
    public final static String[] COMPRESSION_FORMAT = 
    { "Unknown or unspecified format",                                // 0
         "PCM audio in integer format",                               // 1
         "Microsoft adaptive PCM",                                    // 2
         "PCM audio in IEEE floating-point format",                   // 3
         "VSELP codec for Windows CE 2.0 device",                     // 4
         "IBM CVSD",                                                  // 5
         "Microsoft ALAW",                                            // 6
         "Microsoft MULAW",                                           // 7
         "Microsoft DTS",                                             // 8
         "Microsoft Digital Rights Managed encrypted audio",          // 9
         "Microsoft Speech audio codec",                              // 0XA
         "Windows Media RT Voice",                                    // 0xB
         "OKI ADPCM",                                                 // 0X10
         "Intel ADPCM",                                               // 0X11
         "Videologic Systems ADPCM",                                  // 0X12
         "Sierra ADPCM",                                              // 0X13
         "Antex ADPCM",                                               // 0X14
         "DSP Solutions DIGISTD",                                     // 0X15
         "DSP Solutions DIGIFIX",                                     // 0X16
         "OKI ADPCM chips or firmware",                               // 0X17
         "ADPCM for Jazz 16 chip set",                                // 0X18
         "HP CU Codec",                                               // 0X19
         "HP Dynamic Voice",                                          // 0X1A
         "Yamaha ADPCM",                                              // 0X20
         "Speech Compression SONARC",                                 // 0X21
         "DSP Group True Speech",                                     // 0X22
         "Echo Speech SC1",                                           // 0X23
         "Ahead Audio File AF36",                                     // 0X24
         "Audio Processing Technology APTX",                          // 0X25
         "Ahead Audio File AF10",                                     // 0X26
         "Prosody CTI speech card",                                   // 0X27
         "Merging Technologies LRC",                                  // 0X28
         "Dolby AC2",                                                 // 0X30
         "Microsoft GSM610",                                          // 0X31
         "Microsoft MSN audio codec",                                 // 0X32
         "Antex ADPCME",                                              // 0X33
         "Control Resources VQLPC",                                   // 0X34
         "DSP Solutions Digireal",                                    // 0X35
         "DSP Solutions DIGIADPCM",                                   // 0X36
         "Control Resources CR10",                                    // 0X37
         "Natural Microsystems VBXADPCM",                             // 0X38
         "Roland RDAC",                                               // 0X39
         "Echo Speech SC3",                                           // 0X3A
         "Rockwell ADPCM",                                            // 0X3B
         "Rockwell DIGITALK",                                         // 0X3C
         "Xebec Multimedia Solutions",                                // 0X3D
         "Antex G721 ADPCM",                                          // 0X40
         "Antex G728 CELP",                                           // 0X41
         "Microsoft MSG723",                                          // 0X42
         "Microsoft MSG723.1",                                        // 0X43
         "Microsoft MSG729",                                          // 0X44
         "Microsoft MSG726",                                          // 0X45
         "Microsoft MPEG",                                            // 0X50
         "InSoft RT24",                                               // 0X52
         "InSoft PAC",                                                // 0X53
         "ISO/MPEG Layer 3 format tag",                               // 0X55
         "Lucent G723",                                               // 0X59
         "Cirrus Logic",                                              // 0X60
         "ESS PCM",                                                   // 0X61
         "Voxware",                                                   // 0X62
         "Canopus ATRACWAVEFORMAT",                                   // 0X63
         "APICOM G726 ADPCM",                                         // 0X64
         "APICOM G722 ADPCM",                                         // 0X65
         "Microsoft DSAT Display",                                    // 0X67
         "Voxware Byte Aligned",                                      // 0X69
         "Voxware AC8",                                               // 0X70
         "Voxware AC10",                                              // 0X71
         "Voxware AC16",                                              // 0X72
         "Voxware AC20",                                              // 0X73
         "Voxware RT24",                                              // 0X74
         "Voxware RT29",                                              // 0X75
         "Voxware RT29HW",                                            // 0X76
         "Voxware VR12",                                              // 0X77
         "Voxware VR18",                                              // 0X78
         "Voxware TQ40",                                              // 0X79
         "Voxware SC3 (7A)",                                          // 0X7A
         "Voxware SC3 (7B)",                                          // 0X7B
         "SoftSound",                                                 // 0X80
         "Voxware TQ60",                                              // 0X81
         "Microsoft MSRT24",                                          // 0X82
         "AT&T G729A",                                                // 0X83
         "Motion Pixels MVI2",                                        // 0X84
         "Datafusion Systems G726",                                   // 0X85
         "Datafusion Systems GSM610",                                 // 0X86
         "Iterated Systems ISI Audio",                                // 0X88
         "OnLive",                                                    // 0X89
         "Multitude FT SX20",                                         // 0X8A
         "G.721 ADPCM",                                               // 0X8B
         "Convedia G729",                                             // 0X8C
         "Congruency Audio Codec",                                    // 0X8D
         "Siemens SBC24",                                             // 0X91
         "Sonic Foundry Dolby AC3 SPDIF",                             // 0X92
         "MediaSonic G723",                                           // 0x93,
         "Prosody CTI speech card",                                   // 0X94,
         "ZyXEL ADPCM",                                               // 0X97,
         "Philips LPCBB",                                             // 0X98,
         "Studer Professional Audio Packed",                          // 0X99,
         "Phony Talk",                                                // 0XA0,
         "Racal Recorder GSM",                                        // 0XA1,
         "Racal Recorder G720.a",                                     // 0XA2,
         "Racal G723.1",                                              // 0XA3,
         "Racal Tetra ACELP",                                         // 0XA4,
         "NEC AAC",                                                   // 0XB0,
         "Rhetorex ADPCM wave format type",                           // 0X100,
         "BeCubed IRAT",                                              // 0x101,
         "Vivo G723",                                                 // 0X111,
         "Vivo Siren",                                                // 0X112,
         "Philips CELP",                                              // 0X120,
         "Philips Grundig",                                           // 0X121,
         "DEC G723",                                                  // 0X123,
         "SANYO LD-ADPCM wave type",                                  // 0X125,
         "Sipro Lab ACELPNET",                                        // 0X130,
         "Sipro Lab ACELP4800",                                       // 0X131,
         "Sipro Lab ACELP8V3",                                        // 0X132,
         "Sipro Lab ACELPG729",                                       // 0X133,
         "Sipro Lab ACELPG729A",                                      // 0X134,
         "Sipro Lab Kelvin",                                          // 0X135,
         "VoiceAge AMR",                                              // 0X136,
         "Dictaphone G726 ADPCM",                                     // 0X140,
         "Dictaphone CELP68",                                         // 0X141,
         "Dictaphone CELP54",                                         // 0X142,
         "Qualcomm Pure Voice",                                       // 0X150,
         "Qualcomm Half Rate",                                        // 0X151,
         "Related to GSM 6.10",                                       // 0x155,
         "Microsoft Audio 1",                                         // 0X160,
         "Microsoft Audio 2",                                         // 0X161,
         "Microsoft Multichannel WMA",                                // 0X162,
         "WMA lossless",                                              // 0x163
         "WMA Pro over S/PDIF",                                       // 0x164
         "Unisys ADPCM",                                              // 0X170,
         "Unisys ULAW",                                               // 0X171,
         "Unisys ALAW",                                               // 0X172,
         "Unisys NAP 16K",                                            // 0X173,
         "SyCom ACM SYC008",                                          // 0X174,
         "SyCom ACM SYC701 G726L",                                    // 0X175,
         "SyCom ACM SYC701 CELP54",                                   // 0X176,
         "SyCom ACM SYC701 CELP68",                                   // 0X177
         "Knowledge Adventure ADPCM",                                 // 0X178
         "Fraunhofer IIS MPEC 2AAC",                                  // 0X180
         "Digital Theater Systems DS",                                // 0X190,
         "Creative Labs ADPCM",                                       // 0X200
         "Fast Speech 8",                                             // 0X202
         "Fast Speech 10",                                            // 0X203
         "UHER ADPCM",                                                // 0X210
         "Quarterdeck",                                               // 0X220
         "I-Link VC",                                                 // 0X230
         "Aureal Raw Sport",                                          // 0x240
         "Interactive Products HSX",                                  // 0x250
         "Interactive Products RPELP",                                // 0x251
         "Cs2",                                                       // 0X260
         "Sony SCX",                                                  // 0X270
         "Sony SCY",                                                  // 0X271
         "Sony ATRAC3",                                               // 0X272
         "Sony SPC",                                                  // 0X273
         "Telum",                                                     // 0X280
         "Telum IA",                                                  // 0X281
         "Norcom Voice Systems ADPCM",                                // 0x285
         "Fujitsu FM Towns SND",                                      // 0X300
         "Fujitsu (301)",                                             // 0x301
         "Fujitsu (302)",                                             // 0x302
         "Fujitsu (303)",                                             // 0x303
         "Fujitsu (304)",                                             // 0x304
         "Fujitsu (305)",                                             // 0x305
         "Fujitsu (306)",                                             // 0x306
         "Fujitsu (307)",                                             // 0x307
         "Fujitsu (308)",                                             // 0x308
         "Micronas Development",                                      // 0x350
         "Micronas CELP833",                                          // 0x351
         "Brooktree digital audio format",                            // 0x400
         "QDesign Music",                                             // 0x450
         "AT&T VMPCM",                                                // 0x680
         "AT&T TPC",                                                  // 0x681
         "Olivetti SM",                                               // 0x1000
         "Olivetti PCM",                                              // 0x1001
         "Olivetti CELP",                                             // 0x1002
         "Olivetti SBC",                                              // 0x1003
         "Olivetti OPR",                                              // 0x1004
         "Lernout & Hauspie Codec",                                   // 0x1100
         "Lernout & Hauspie CELP",                                    // 0x1101
         "Lernout & Hauspie SB8",                                     // 0x1102
         "Lernout & Hauspie SB12",                                    // 0x1103
         "Lernout & Hauspie SB16",                                    // 0x1104
         "Norris",                                                    // 0x1400
         "AT&T Soundspace Musicompress",                              // 0x1500
         
         "Sonic Foundry Lossless",                                    // 0x1971
         "Innings ADPCM",                                             // 0X1979
         "FAST Multimedia DVM",                                       // 0x2000
         "Reserved rangle to 0x2600",                                 // 0x2500
         "Divio's AAC",                                               // 0x4143
         "Nokia adaptive multirate",                                  // 0x4201
         "Divio's G726",                                              // 0x4243
         "3Com NBX",                                                  // 0x7000
         "Adaptive multirate",                                        // 0x7a21
         "AMR with silence detection",                                // 0x7a22
         "Comverse G723.1",                                           // 0xa100
         "Comverse AVQSBC",                                           // 0xa101
         "Comverse old SBC",                                          // 0xa102
         "Symbol Technology's G729A",                                 // 0xa103
         "Voice Age AMR WB",                                          // 0xa104
         "Ingenient's G726",                                          // 0xa105
         "ISO/MPEG-4 advanced audio Coding",                          // 0xa106
         "Encore Software Ltd's G726",                                // 0xa107
         "Extensible Wave format"                                     // 0xfffe
    };


   public final static int[] COMPRESSION_INDEX = 
   {
          0,
          1,
          2,
          3,
          4,
          5,
          6,
          7,
          8,
          9,
          0XA,
          0xB,
          0X10,
          0X11,
          0X12,
          0X13,
          0X14,
          0X15,
          0X16,
          0X17,
          0X18,
          0X19,
          0X1A,
          0X20,
          0X21,
          0X22,
          0X23,
          0X24,
          0X25,
          0X26,
          0X27,
          0X28,
          0X30,
          0X31,
          0X32,
          0X33,
          0X34,
          0X35,
          0X36,
          0X37,
          0X38,
          0X39,
          0X3A,
          0X3B,
          0X3C,
          0X3D,
          0X40,
          0X41,
          0X42,
          0X43,
          0X44,
          0X45,
          0X50,
          0X52,
          0X53,
          0X55,
          0X59,
          0X60,
          0X61,
          0X62,
          0X63,
          0X64,
          0X65,
          0X67,
          0X69,
          0X70,
          0X71,
          0X72,
          0X73,
          0X74,
          0X75,
          0X76,
          0X77,
          0X78,
          0X79,
          0X7A,
          0X7B,
          0X80,
          0X81,
          0X82,
          0X83,
          0X84,
          0X85,
          0X86,
          0X88,
          0X89,
          0X8A,
          0X8B,
          0X8C,
          0X8D,
          0X91,
          0X92,
          0x93,
          0X94,
          0X97,
          0X98,
          0X99,
          0XA0,
          0XA1,
          0XA2,
          0XA3,
          0XA4,
          0XB0,
          0X100,
          0x101,
          0X111,
          0X112,
          0X120,
          0X121,
          0X123,
          0X125,
          0X130,
          0X131,
          0X132,
          0X133,
          0X134,
          0X135,
          0X136,
          0X140,
          0X141,
          0X142,
          0X150,
          0X151,
          0x155,
          0X160,
          0X161,
          0X162,
          0x163,
          0x164,
          0X170,
          0X171,
          0X172,
          0X173,
          0X174,
          0X175,
          0X176,
          0X177,
          0X178,
          0X180,
          0X190,
          0X200,
          0X202,
          0X203,
          0X210,
          0X220,
          0X230,
          0x240,
          0x250,
          0x251,
          0X260,
          0X270,
          0X271,
          0X272,
          0X273,
          0X280,
          0X281,
          0x285,
          0X300,
          0x301,
          0x302,
          0x303,
          0x304,
          0x305,
          0x306,
          0x307,
          0x308,
          0x350,
          0x351,
          0x400,
          0x450,
          0x680,
          0x681,
          0x1000,
          0x1001,
          0x1002,
          0x1003,
          0x1004,
          0x1100,
          0x1101,
          0x1102,
          0x1103,
          0x1104,
          0x1400,
          0x1500,
          0x1971,
          0X1979,
          0x2000,
          0x2500,
          0x4143,
          0x4201,
          0x4243,
          0x7000,
          0x7a21,
          0x7a22,
          0xa100,
          0xa101,
          0xa102,
          0xa103,
          0xa104,
          0xa105,
          0xa106,
          0xa107,
          0xfffe
   };

    /** Strings for SMPTE formats in the Sample Chunk */
    public final static String[] SMPTE_FORMAT = 
    {
        "No SMPTE offset",
        "24 frames per second",
        "25 frames per second",
        "30 frames per second with frame dropping",
        "30 frames per second"
    };
    
    /** Indices for SMPTE formats in the Sample Chunk */
    public final static int[] SMPTE_FORMAT_INDEX =
    { 0, 24, 25, 29, 30 };

    /** Flags for SoundInformation bits in the MPEG chunk,
     *  "1" values */
    public final static String[] SOUND_INFORMATION_1 =
    {
        "Non-homogeneous sound data",
        "Padding bit always 0",
        "Sample frequency 22.05 or 44.1 KHz",
        "Free format is used"
    };


    /** Flags for SoundInformation bits in the MPEG chunk,
     *  "0" values */
    public final static String[] SOUND_INFORMATION_0 =
    {
        "Homogeneous sound data",
        "Padding bit may alternate",
        "",
        "No free format audio frame"
    };
    
    /** Flags for ancillary data definition in the MPEG chunk,
     *  "1" values
     */
    public final static String[] ANCILLARY_DEF_1 =
    {
        "Energy of left channel present",
        "Private byte is free for internal use"
    };


    /** Flags for ancillary data definition in the MPEG chunk,
     *  "0" values
     */
    public final static String[] ANCILLARY_DEF_0 =
    {
        "Energy of left channel absent",
        "No private byte free for internal use"
    };
}
