package com.webank.plugins.artifacts.support.cmdb.dto.v2;

import java.util.List;
import java.util.Map;

import com.webank.plugins.artifacts.support.cmdb.dto.CmdbResponse;

public class CmdbResponses {

    public static class ImageInfoResponse extends CmdbResponse<ImageInfoDto> {
    }

    public static class ConstantsReferenceTypesResponse extends CmdbResponse<List<String>> {
    }

    public static class ConstantsCiStatusResponse extends CmdbResponse<List<String>> {
    }

    public static class EnumCategoryTypeQueryResultResponse extends CmdbResponse<PaginationQueryResult<CatTypeDto>> {
    }

    public static class EnumCategoryTypeListResultResponse extends CmdbResponse<List<CatTypeDto>> {
    }

    public static class EnumCategoryQueryResultResponse extends CmdbResponse<PaginationQueryResult<CategoryDto>> {
    }

    public static class EnumCategoryListResultResponse extends CmdbResponse<List<CategoryDto>> {
    }

    public static class EnumCodeQueryResultResponse extends CmdbResponse<PaginationQueryResult<CatCodeDto>> {
    }

    public static class EnumCodeListResultResponse extends CmdbResponse<List<CatCodeDto>> {
    }

    public static class CiTypeQueryResultResponse extends CmdbResponse<PaginationQueryResult<CiTypeDto>> {
    }

    public static class CiTypeListResultResponse extends CmdbResponse<List<CiTypeDto>> {
    }

    public static class CiTypeAttributeQueryResultResponse extends CmdbResponse<PaginationQueryResult<CiTypeAttrDto>> {
    }

    public static class CiTypeAttributeListResultResponse extends CmdbResponse<List<CiTypeAttrDto>> {
    }

    public static class CiTypeDataQueryResultResponse extends CmdbResponse<PaginationQueryResult<Object>> {
    }

    public static class CiTypeDataListResultResponse extends CmdbResponse<List<Object>> {
    }

    public static class CiDataQueryResultResponse extends CmdbResponse<PaginationQueryResult<Object>> {
    }

    public static class CiDataListResultResponse extends CmdbResponse<List<Object>> {
    }

    public static class CiReferenceDataListResultResponse extends CmdbResponse<PaginationQueryResult<Object>> {
    }

    public static class CiDataVersionsQueryResultResponse extends CmdbResponse<List<String>> {
    }

    public static class CiDataVersionDetailResultResponse extends CmdbResponse<List<CiDataTreeDto>> {
    }

    public static class IntQueryExecuteDataResponse extends CmdbResponse<PaginationQueryResult<Map<String, Object>>> {
    }

    public static class AdhocIntegrationQueryDataResponse extends CmdbResponse<PaginationQueryResult<Map<String, Object>>> {
    }

    public static class QueryOperationDataResponse extends CmdbResponse<List<String>> {
    }
    
    public static class SpecialConnectorDtoResponse extends CmdbResponse<List<Map<String,Object>>> {
    }
}
