package org.onosproject.wisesdn;

import org.onlab.rest.AbstractWebApplication;
import java.util.Set;

/**
 * SDN-WISE Web Application
 */
public class WiseWebApplication extends AbstractWebApplication {
    @Override
    public Set<Class<?>> getClasses() {
        return getClasses(WiseWebResource.class);
    }
}
