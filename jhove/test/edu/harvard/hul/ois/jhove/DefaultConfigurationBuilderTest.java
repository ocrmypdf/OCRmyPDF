package edu.harvard.hul.ois.jhove;

import static org.junit.Assert.*;

import org.junit.Test;

import edu.harvard.hul.ois.jhove.module.TiffModule;

public class DefaultConfigurationBuilderTest {


    
    @Test
    public void testDefaultConfigParameters () {
        DefaultConfigurationBuilder dcb = new DefaultConfigurationBuilder (null);
        String[] param = dcb.getDefaultConfigParameters(TiffModule.class);
        assertEquals ("byteoffset=true", param[0]);
    }

}
