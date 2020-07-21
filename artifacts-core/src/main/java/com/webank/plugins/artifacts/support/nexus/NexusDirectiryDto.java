package com.webank.plugins.artifacts.support.nexus;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.AbstractResourceDto;
import lombok.Data;

@JsonInclude(JsonInclude.Include.NON_NULL)
@Data
public class NexusDirectiryDto extends AbstractResourceDto {

    private String name;
    private String downloadUrl;
}
