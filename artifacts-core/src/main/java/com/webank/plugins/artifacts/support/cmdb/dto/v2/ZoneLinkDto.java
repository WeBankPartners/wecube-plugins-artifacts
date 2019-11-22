package com.webank.plugins.artifacts.support.cmdb.dto.v2;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonInclude;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@JsonInclude(JsonInclude.Include.NON_EMPTY)
@NoArgsConstructor
@AllArgsConstructor
public class ZoneLinkDto {
    private String idcGuid;
    private List<Object> linkList;
}

