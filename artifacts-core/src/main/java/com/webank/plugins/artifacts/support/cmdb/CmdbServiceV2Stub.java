package com.webank.plugins.artifacts.support.cmdb;

import static com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery.defaultQueryObject;
import static org.apache.commons.collections4.CollectionUtils.isNotEmpty;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import com.webank.plugins.artifacts.commons.ApplicationProperties;
import com.webank.plugins.artifacts.support.cmdb.dto.CmdbResponse;
import com.webank.plugins.artifacts.support.cmdb.dto.CmdbResponse.DefaultCmdbResponse;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CatCodeDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CategoryDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CiDataDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CiDataTreeDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CiTypeAttrDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CiTypeDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CmdbResponses;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CmdbResponses.CiDataQueryResultResponse;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CmdbResponses.CiDataVersionDetailResultResponse;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CmdbResponses.CiTypeAttributeQueryResultResponse;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CmdbResponses.CiTypeQueryResultResponse;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CmdbResponses.EnumCategoryQueryResultResponse;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CmdbResponses.EnumCodeListResultResponse;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CmdbResponses.EnumCodeQueryResultResponse;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CmdbResponses.SpecialConnectorDtoResponse;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.ImageInfoDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.OperateCiDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQueryResult;

@Service
public class CmdbServiceV2Stub {
	
    private static final String pluginContextPath = "/wecmdb";

    private static final String CONSTANT_CI_TYPE_ID = "ciTypeId";

    private static final String CONSTANT_CAT_ID = "catId";
    private static final String CONSTANT_SEQ_NO = "seqNo";
    private static final String CONSTANT_ATTRIBUTES = "attributes";
    private static final String CONSTANT_OPERATION = "?operation=";

    private static final String API_VERSION = "/api/v2";

    private static final String FILE_UPLOAD = "/image/upload";

    private static final String ENUM_CATEGORY_QUERY = "/enum/cats/retrieve";

    private static final String ENUM_CODE_CREATE = "/enum/codes/create";
    private static final String ENUM_CODE_QUERY = "/enum/codes/retrieve";
    
    private static final String CITYPE_ATTRIBUTE_QUERY = "/ciTypeAttrs/retrieve";


    private static final String CITYPE_QUERY = "/ciTypes/retrieve";

    private static final String CIDATA_CREATE = "/ci/%d/create";
    private static final String CIDATA_QUERY = "/ci/%d/retrieve";
    private static final String CIDATA_UPDATE = "/ci/%d/update";
    private static final String CIDATA_DELETE = "/ci/%d/delete";
    private static final String CIDATA_STATE_OPERATE = "/ci/state/operate";
    private static final String CIDATA_RETRIEVE_VERSION_DETAIL = "/ci/from/%d/to/%d/versions/%s/retrieve";
    private static final String QUERY_SPECIAL_CONNECTOR = "/static-data/special-connector";
    
    @Autowired
    private CmdbRestTemplate template;

    @Autowired
    private ApplicationProperties applicationProperties;

    public Integer uploadFile(Resource inputStreamSource) {
        ImageInfoDto imageInfo = template.uploadSingleFile(asCmdbUrl(FILE_UPLOAD), "img", inputStreamSource,
                CmdbResponses.ImageInfoResponse.class);
        return imageInfo.getId();
    }

    public CategoryDto getEnumCategoryByName(String categoryName) {
        return findFirst(ENUM_CATEGORY_QUERY, "catName", categoryName, EnumCategoryQueryResultResponse.class);
    }

    public List<CatCodeDto> createEnumCodes(CatCodeDto... catCodeDtos) {
        return create(ENUM_CODE_CREATE, catCodeDtos, EnumCodeListResultResponse.class);
    }

    public PaginationQueryResult<CatCodeDto> queryEnumCodes(PaginationQuery queryObject) {
        return query(ENUM_CODE_QUERY, queryObject, EnumCodeQueryResultResponse.class);
    }

    public List<CatCodeDto> getEnumCodesByCategoryId(Integer categoryId) {
        PaginationQueryResult<CatCodeDto> queryResult = query(ENUM_CODE_QUERY,
                defaultQueryObject(CONSTANT_CAT_ID, categoryId).ascendingSortBy(CONSTANT_SEQ_NO), EnumCodeQueryResultResponse.class);
        return queryResult.getContents();
    }

    public List<CiTypeDto> getAllCiTypes(boolean withAttributes, String status) {
        PaginationQuery paginationQuery = defaultQueryObject();

        if (status != null) {
            paginationQuery = paginationQuery.addInFilter("status", Arrays.asList(status.split(",")));
        }

        if (withAttributes) {
            paginationQuery = paginationQuery.addReferenceResource(CONSTANT_ATTRIBUTES);
            if (status != null) {
                paginationQuery = paginationQuery.addInFilter("attributes.status", Arrays.asList(status.split(",")));
            }
        }

        PaginationQueryResult<CiTypeDto> queryResult = query(CITYPE_QUERY, paginationQuery.ascendingSortBy(CONSTANT_SEQ_NO),
                CiTypeQueryResultResponse.class);
        return queryResult.getContents();
    }

    public List<CiDataDto> createCiData(Integer ciTypeId, Object ciData) {
        ArrayList<Object> ciDatas = new ArrayList<Object>();
        ciDatas.add(ciData);
        return create(formatString(CIDATA_CREATE, ciTypeId), ciDatas.toArray(), DefaultCmdbResponse.class);
    }

    public PaginationQueryResult<Object> queryCiData(Integer ciTypeId, PaginationQuery queryObject) {
        return query(formatString(CIDATA_QUERY, ciTypeId), queryObject, CiDataQueryResultResponse.class);
    }

    public List<CiDataTreeDto> getCiDataDetailForVersion(int fromCiTypeId, int toCiTypeId, String version) {
        return query(formatString(CIDATA_RETRIEVE_VERSION_DETAIL, fromCiTypeId, toCiTypeId, version),
                defaultQueryObject(), CiDataVersionDetailResultResponse.class);
    }

    public List<Object> updateCiData(Integer ciTypeId, Map<String, Object> ciData) {
        List<Map<String, Object>> ciDatas = new ArrayList<Map<String, Object>>();
        ciDatas.add(ciData);
        return update(formatString(CIDATA_UPDATE, ciTypeId), ciDatas.toArray(), DefaultCmdbResponse.class);
    }

    public Object deleteCiData(Integer ciTypeId, List<String> ids) {
        return delete(formatString(CIDATA_DELETE, ciTypeId), ids.toArray(), DefaultCmdbResponse.class);
    }

    public Object operateCiForState(List<OperateCiDto> operateCiObject, String operation) {
        return template.postForResponse(asCmdbUrl(CIDATA_STATE_OPERATE) + CONSTANT_OPERATION + operation, operateCiObject, DefaultCmdbResponse.class);
    }

    private <D, R extends CmdbResponse<?>> D findFirst(String url, String field, Object value, Class<R> responseType) {
        return findFirst(url, defaultQueryObject(field, value), responseType, true);
    }

    private <D, R extends CmdbResponse<?>> D findFirst(String url, PaginationQuery queryObject, Class<R> responseType, boolean dataRequired) {
        String targetUrl = asCmdbUrl(url);
        PaginationQueryResult<D> result = template.postForResponse(targetUrl, queryObject, responseType);
        List<D> dataContent = result.getContents();
        if (isNotEmpty(dataContent))
            return dataContent.get(0);
        if (dataRequired)
            throw new CmdbDataNotFoundException(String.format("Data not found in location [%s] with query parameter %s", url, queryObject));
        return null;
    }

    private <D, R extends CmdbResponse<?>> D create(String url, Object[] createObject, Class<R> responseType) {
        return template.postForResponse(asCmdbUrl(url), createObject, responseType);
    }

    private <D, R extends CmdbResponse<?>> D query(String url, PaginationQuery queryObject, Class<R> responseType) {
        return template.postForResponse(asCmdbUrl(url), queryObject, responseType);
    }

    private <D, R extends CmdbResponse<?>> D update(String url, Object[] updateObject, Class<R> responseType) {
        return template.postForResponse(asCmdbUrl(url), updateObject, responseType);
    }

    private <D, R extends CmdbResponse<?>> D delete(String url, Object[] ids, Class<R> responseType) {
        return template.postForResponse(asCmdbUrl(url), ids, responseType);
    }

    private String asCmdbUrl(String path, Object... pathVariables) {
        if (pathVariables != null && pathVariables.length > 0) {
            path = String.format(path, pathVariables);
        }
        return applicationProperties.getWecubeGatewayServerUrl() + pluginContextPath + API_VERSION + path;
    }

    private String formatString(String path, Object... pathVariables) {
        if (pathVariables != null && pathVariables.length > 0) {
            path = String.format(path, pathVariables);
        }
        return path;
    }
    public List<CiTypeAttrDto> queryCiTypeAttributes(PaginationQuery queryObject) {
        PaginationQueryResult<CiTypeAttrDto> queryResult = query(CITYPE_ATTRIBUTE_QUERY, queryObject, CiTypeAttributeQueryResultResponse.class);
        return queryResult.getContents();
    }
    
    public List<CiTypeAttrDto> getCiTypeAttributesByCiTypeId(Integer ciTypeId) {
        return queryCiTypeAttributes(defaultQueryObject(CONSTANT_CI_TYPE_ID, ciTypeId).ascendingSortBy("displaySeqNo"));
    }

    public List<SpecialConnectorDtoResponse> getSpecialConnector() {
        List<SpecialConnectorDtoResponse> queryResult = template.get(asCmdbUrl(QUERY_SPECIAL_CONNECTOR), SpecialConnectorDtoResponse.class);
        return queryResult;
    }

}
