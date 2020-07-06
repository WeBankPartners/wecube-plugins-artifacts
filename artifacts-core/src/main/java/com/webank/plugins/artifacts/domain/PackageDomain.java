package com.webank.plugins.artifacts.domain;

import lombok.Data;

import java.util.List;

@Data
public class PackageDomain {
    private List<String> configFilesWithPath;
    private String deployFile;
    private String startFile;
    private String stopFile;
    private String isDecompression;

}
