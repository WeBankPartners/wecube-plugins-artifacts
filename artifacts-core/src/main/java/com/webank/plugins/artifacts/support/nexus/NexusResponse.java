package com.webank.plugins.artifacts.support.nexus;

import lombok.Data;

@Data
public class NexusResponse<DATATYPE> {
    public static final String STATUS_CODE_OK = "OK";

    private DATATYPE items;

}
