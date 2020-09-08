package com.webank.plugins.artifacts.service;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.configurationprocessor.json.JSONException;
import org.springframework.boot.configurationprocessor.json.JSONObject;
import org.springframework.stereotype.Service;
import org.springframework.web.util.UriComponentsBuilder;

import com.webank.plugins.artifacts.commons.PluginException;
import com.webank.plugins.artifacts.interceptor.AuthorizationStorage;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQueryResult;
import com.webank.plugins.artifacts.support.nexus.NexusAssetItemInfo;
import com.webank.plugins.artifacts.support.nexus.NexusClient;
import com.webank.plugins.artifacts.support.nexus.NexusDirectiryDto;
import com.webank.plugins.artifacts.support.nexus.NexusSearchAssetResponse;
import com.webank.plugins.artifacts.utils.Base64Utils;

@Service
public class NexusArtifactManagementService extends AbstractArtifactService{
    private static final Logger log = LoggerFactory.getLogger(NexusArtifactManagementService.class);

    private static final String NEXUS_SEARCH_ASSET_API_PATH = "/service/rest/beta/search/assets";
    
    @Autowired
    private NexusClient nexusClient;
    
    public List<NexusDirectiryDto> queryNexusDirectory(String unitDesignId, PaginationQuery queryObject){
        String artifactPath = calculateArtifactPath(unitDesignId, queryObject);
        return doQueryNexusDirectory(artifactPath);
    }
    
    public void asyncUploadNexusPackageToS3(String unitDesignId, String downloadUrl,String uploadName) {
        ExecutorService executor = Executors.newFixedThreadPool(1);
        String authorization = AuthorizationStorage.getIntance().get();
        executor.submit(new Runnable() {
            @Override
            public void run() {
                try {
                    log.info("sync upload NEXUS package to S3 begin");
                    File file = convertNexusPackageToFile(downloadUrl,downloadUrl.substring(downloadUrl.lastIndexOf("/") + 1));
                    String url = uploadPackageToS3(file);
                    savePackageToCmdb(file, unitDesignId, uploadName, url, authorization);
                    log.info("sync upload NEXUS package to S3 end");
                } catch (Exception e) {
                    log.info("sync upload NEXUS package to S3 failed ,", e);
                }
            }
        });
    }
    
    private File convertNexusPackageToFile(String downloadUrl,String fileName) {
        File file = new File(fileName);
        try {
            URL url = new URL(downloadUrl);
            URLConnection connection = url.openConnection();
            connection.setConnectTimeout(5 * 1000);
            connection.setRequestProperty("Authorization","Basic " + Base64Utils.getBASE64(applicationProperties.getArtifactsNexusUsername() + ":" + applicationProperties.getArtifactsNexusPassword()));
            InputStream inputStream = connection.getInputStream();
            byte[] byteArr = new byte[1024];
            int len;
            FileOutputStream fos = new FileOutputStream(file);
            while ((len = inputStream.read(byteArr)) != -1) {
                fos.write(byteArr, 0, len);
            }
            fos.close();
            inputStream.close();
        } catch (IOException e) {
            log.error("errors while convert nexus package file.", e);
            throw new PluginException("3003", "Failed to convert Nexus package to file.");
        }
       return file;
    }
    
    private List<NexusDirectiryDto> doQueryNexusDirectory(String artifactPath) {
        if (artifactPath == null || artifactPath.isEmpty()) {
            throw new PluginException("Upload artifact path is required.");
        }

        // configuration parameters
        // String filter = "jar,zip";

        String nexusBaseUrl = applicationProperties.getArtifactsNexusServerUrl();
        String nexusRepository = applicationProperties.getArtifactsNexusRepository();
        String nexusSearchAssetApiUrl = nexusBaseUrl + NEXUS_SEARCH_ASSET_API_PATH;
        UriComponentsBuilder b = UriComponentsBuilder.fromHttpUrl(nexusSearchAssetApiUrl);
        b = b.queryParam("repository", nexusRepository);
        String group = null;
        if (StringUtils.isNoneBlank(artifactPath)) {
            group = artifactPath;
            if (!artifactPath.startsWith("/")) {
                group = "/" + group;
            }

            b = b.queryParam("group", group);
        }

        List<NexusDirectiryDto> results = new ArrayList<>();
        NexusSearchAssetResponse nexusSearchAssetResponse = nexusClient.searchAsset(b.build().toUri(),
                applicationProperties.getArtifactsNexusUsername(), applicationProperties.getArtifactsNexusPassword());

        String continuationToken = nexusSearchAssetResponse.getContinuationToken();
        List<NexusAssetItemInfo> assetItems = nexusSearchAssetResponse.getItems();
        for (NexusAssetItemInfo assetItem : assetItems) {
            if (assetItem.getPath().endsWith("jar") || assetItem.getPath().endsWith("zip")
                    || assetItem.getPath().endsWith("tar") || assetItem.getPath().endsWith("gz")
                    || assetItem.getPath().endsWith("tgz")) {
                NexusDirectiryDto directiryDto = new NexusDirectiryDto();
                directiryDto.setDownloadUrl(assetItem.getDownloadUrl());
                directiryDto
                        .setName(assetItem.getDownloadUrl().substring(assetItem.getDownloadUrl().lastIndexOf("/") + 1));
                results.add(directiryDto);
            }
        }

        while (StringUtils.isNoneBlank(continuationToken)) {
            b = UriComponentsBuilder.fromHttpUrl(nexusSearchAssetApiUrl);
            b = b.queryParam("repository", nexusRepository);
            if(StringUtils.isNoneBlank(group)){
                b = b.queryParam("group", group);
            }
            b = b.queryParam("continuationToken", continuationToken);

            nexusSearchAssetResponse = nexusClient.searchAsset(b.build().toUri(),
                    applicationProperties.getArtifactsNexusUsername(),
                    applicationProperties.getArtifactsNexusPassword());

            List<NexusAssetItemInfo> queryAssetItems = nexusSearchAssetResponse.getItems();
            for (NexusAssetItemInfo assetItem : queryAssetItems) {
                if (assetItem.getPath().endsWith("jar") || assetItem.getPath().endsWith("zip")) {
                    NexusDirectiryDto directiryDto = new NexusDirectiryDto();
                    directiryDto.setDownloadUrl(assetItem.getDownloadUrl());
                    directiryDto.setName(
                            assetItem.getDownloadUrl().substring(assetItem.getDownloadUrl().lastIndexOf("/") + 1));
                    results.add(directiryDto);
                }
            }

            continuationToken = nexusSearchAssetResponse.getContinuationToken();
        }
        return results;

    }
    
    @SuppressWarnings({ "unchecked", "rawtypes" })
    private String calculateArtifactPath(String unitDesignId, PaginationQuery queryObject) {
        if (StringUtils.isBlank(unitDesignId)) {
            throw new PluginException("Unit design ID cannot be blank.");
        }
        String artifactPath = null;
        queryObject.addEqualsFilter("guid", unitDesignId);
        PaginationQueryResult<Object> objectPaginationQueryResult = cmdbServiceV2Stub
                .queryCiData(cmdbDataProperties.getCiTypeIdOfUnitDesign(), queryObject);

        if (objectPaginationQueryResult == null || objectPaginationQueryResult.getContents() == null
                || objectPaginationQueryResult.getContents().size() <= 0) {
            return artifactPath;
        }
        try {
            Map<String, String> ResultMap = (Map) objectPaginationQueryResult.getContents().get(0);
            JSONObject responseJson = (JSONObject) JSONObject.wrap(ResultMap.get("data"));
            // JSONObject unit_design =
            // responseJson.getJSONObject(applicationProperties.getCmdbArtifactPath());
            artifactPath = responseJson.getString(applicationProperties.getCmdbArtifactPath());
        } catch (JSONException e) {
            log.error("Can not parse CMDB Response json", e);
            throw new PluginException("3006","Cannot find Nexus path from CMDB.Please configure Nexus path in CMDB.");
        }
        return artifactPath;
    }
}
