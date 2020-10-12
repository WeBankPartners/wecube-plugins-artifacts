package com.webank.plugins.artifacts.support.cmdb.dto.v2;

import java.util.List;

public class PaginationQueryResult<DATATYPE> {
    private PageInfo pageInfo;
    private List<DATATYPE> contents;

    public PageInfo getPageInfo() {
        return pageInfo;
    }

    public void setPageInfo(PageInfo pageInfo) {
        this.pageInfo = pageInfo;
    }

    public List<DATATYPE> getContents() {
        return contents;
    }

    public void setContents(List<DATATYPE> contents) {
        this.contents = contents;
    }

    public static class PageInfo {
        private int startIndex;
        private int pageSize;
        private int totalRows;

        public int getStartIndex() {
            return startIndex;
        }

        public void setStartIndex(int startIndex) {
            this.startIndex = startIndex;
        }

        public int getPageSize() {
            return pageSize;
        }

        public void setPageSize(int pageSize) {
            this.pageSize = pageSize;
        }

        public int getTotalRows() {
            return totalRows;
        }

        public void setTotalRows(int totalRows) {
            this.totalRows = totalRows;
        }

    }
}
