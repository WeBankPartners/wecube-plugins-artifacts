package com.webank.plugins.artifacts.support.nexus;

public class NexusAssetItemInfo {
    private String downloadUrl;
    private String path;
    private String id;
    private String repository;
    private String format;

    public String getDownloadUrl() {
        return downloadUrl;
    }

    public void setDownloadUrl(String downloadUrl) {
        this.downloadUrl = downloadUrl;
    }

    public String getPath() {
        return path;
    }

    public void setPath(String path) {
        this.path = path;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getRepository() {
        return repository;
    }

    public void setRepository(String repository) {
        this.repository = repository;
    }

    public String getFormat() {
        return format;
    }

    public void setFormat(String format) {
        this.format = format;
    }

    @Override
    public String toString() {
        StringBuilder builder = new StringBuilder();
        builder.append("NexusAssetItemInfo [downloadUrl=");
        builder.append(downloadUrl);
        builder.append(", path=");
        builder.append(path);
        builder.append(", id=");
        builder.append(id);
        builder.append(", repository=");
        builder.append(repository);
        builder.append(", format=");
        builder.append(format);
        builder.append("]");
        return builder.toString();
    }
}
