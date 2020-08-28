package com.webank.plugins.artifacts.support.nexus;

import java.util.ArrayList;
import java.util.List;

public class NexusSearchAssetResponse {
    private String continuationToken;
    private List<NexusAssetItemInfo> items = new ArrayList<NexusAssetItemInfo>();

    public String getContinuationToken() {
        return continuationToken;
    }

    public void setContinuationToken(String continuationToken) {
        this.continuationToken = continuationToken;
    }

    public List<NexusAssetItemInfo> getItems() {
        return items;
    }

    public void setItems(List<NexusAssetItemInfo> items) {
        this.items = items;
    }
}
