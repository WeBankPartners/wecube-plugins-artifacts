<template>
  <div>
    <!-- 在线上传 -->
    <Modal v-model="onlineModal" :fullscreen="isfullscreen">
      <div slot="header" class="custom-modal-header">
        <span>
          {{ $t('select_online') }}
        </span>
        <Icon v-if="isfullscreen" @click="fullscreenChange" class="fullscreen-icon" type="ios-contract" />
        <Icon v-else @click="fullscreenChange" class="fullscreen-icon" type="ios-expand" />
      </div>
      <Form :label-width="100" ref="onlineUploadRuleValidateRef" :model="onlineUploadParams" :rules="onlineUploadRuleValidate">
        <FormItem :label="$t('filterPath')">
          <span style="vertical-align: middle;">{{ onlineUploadParams.filterPath }}</span>
        </FormItem>
        <FormItem :label="$t('art_package')" prop="downloadUrl">
          <Select filterable clearable v-model="onlineUploadParams.downloadUrl">
            <Option v-for="conf in onlinePackages" :value="conf.downloadUrl" :label="conf.name" :key="conf.downloadUrl">
              <span>{{ conf.name }}</span>
              <span style="float:right;color:#ccc">{{ utcToLocal(conf.lastModified) }}</span>
            </Option>
          </Select>
        </FormItem>
        <FormItem :label="$t('package_type')">
          <Select filterable @on-change="getbaselinePkg('onlineUploadParams')" :placeholder="$t('package_type')" v-model="onlineUploadParams.package_type">
            <Option v-for="item in packageOptions" :value="item.value" :key="item.label">{{ item.label }}</Option>
          </Select>
        </FormItem>
        <FormItem :label="$t('baseline_package')">
          <Select clearable filterable :placeholder="$t('baseline_package')" v-model="onlineUploadParams.baseline_package">
            <Option v-for="conf in baselinePackageOptions" :value="conf.guid" :key="conf.name">{{ conf.name }}</Option>
          </Select>
        </FormItem>
      </Form>
      <div slot="footer">
        <Button @click="onlineModal = false">{{ $t('artifacts_cancel') }}</Button>
        <Button type="primary" :disabled="onlineUploadParams.downloadUrl === ''" :loading="loading" @click="confirmOnlineUpload">{{ $t('art_upload') }}</Button>
      </div>
    </Modal>

    <!-- 本地上传 -->
    <Modal v-model="localModal" :fullscreen="isfullscreen">
      <div slot="header" class="custom-modal-header">
        <span>
          {{ $t('art_upload_artifact_package') }}
        </span>
        <Icon v-if="isfullscreen" @click="fullscreenChange" class="fullscreen-icon" type="ios-contract" />
        <Icon v-else @click="fullscreenChange" class="fullscreen-icon" type="ios-expand" />
      </div>
      <Form :label-width="100">
        <FormItem :label="$t('art_package')">
          <Upload action="" :before-upload="handleUpload" :show-upload-list="false">
            <Button class="btn-upload">
              <img src="@/styles/icon/UploadOutlined.svg" class="upload-icon" />
              {{ $t('artifacts_upload_new_package') }}
            </Button>
          </Upload>
          <span style="word-wrap: break-word;">{{ localUploadParams.fileName }} {{ localUploadParams.size }} </span>
        </FormItem>
        <FormItem :label="$t('package_type')">
          <Select filterable @on-change="getbaselinePkg('localUploadParams')" :placeholder="$t('package_type')" v-model="localUploadParams.package_type">
            <Option v-for="item in packageOptions" :value="item.value" :key="item.value">{{ item.label }}</Option>
          </Select>
        </FormItem>
        <FormItem :label="$t('baseline_package')">
          <Select clearable filterable :placeholder="$t('baseline_package')" v-model="localUploadParams.baseline_package">
            <Option v-for="conf in baselinePackageOptions" :value="conf.guid" :key="conf.name">{{ conf.name }}</Option>
          </Select>
        </FormItem>
      </Form>
      <div slot="footer">
        <Button @click="localModal = false">{{ $t('artifacts_cancel') }}</Button>
        <Button type="primary" :disabled="localUploadParams.fileName === ''" :loading="loading" @click="confirmLocalUpload">{{ $t('art_upload') }}</Button>
      </div>
    </Modal>
  </div>
</template>

<script>
// eslint-disable-next-line no-unused-vars
import { getFilePath, queryArtifactsList, queryPackages, uploadArtifact, uploadLocalArtifact } from '@/api/server.js'
import dayjs from 'dayjs'
export default {
  name: '',
  data () {
    return {
      loading: false,
      isfullscreen: false,
      guid: '', // 当前单元
      uploadType: '', // uploadType: 'local' | 'online'
      packageType: '', // 包类型，外部传入
      onlineModal: false,
      onlineUploadParams: {
        filterPath: '',
        downloadUrl: '',
        package_type: '',
        baseline_package: ''
      },
      onlineUploadRuleValidate: {
        downloadUrl: [{ required: true, message: this.$t('art_package') + this.$t('art_cannot_be_empty'), trigger: 'blur' }]
      },
      onlinePackages: [], // 在线包列表
      baselinePackageOptions: '', // 基线列表
      localModal: false,
      localUploadParams: {
        fileName: '',
        size: '',
        package_type: '',
        baseline_package: ''
      },
      formData: null,
      packageOptions: [
        { label: this.$t('APP&DB'), value: 'APP&DB', num: 0 },
        { label: this.$t('APP'), value: 'APP', num: 0 },
        { label: this.$t('DB'), value: 'DB', num: 0 },
        { label: this.$t('IMAGE'), value: 'IMAGE', num: 0 },
        { label: this.$t('RULE'), value: 'RULE', num: 0 }
      ]
    }
  },
  watch: {},
  props: [],
  methods: {
    utcToLocal (utcDate) {
      return dayjs(utcDate).format('YYYY-MM-DD HH:mm:ss')
    },
    openUploadDialog (uploadType, guid, packageType) {
      this.isfullscreen = false
      this.uploadType = uploadType
      this.guid = guid
      this.onlineUploadParams.package_type = packageType
      this.localUploadParams.package_type = packageType
      if (uploadType === 'online') {
        this.onlineUpload()
      } else {
        this.localUpload()
      }
    },
    async localUpload () {
      this.emptyJsonKey('localUploadParams')
      await this.getbaselinePkg('localUploadParams')
      this.formData = new FormData()
      this.localModal = true
    },
    // 在线包上传
    async onlineUpload () {
      this.$refs['onlineUploadRuleValidateRef'].resetFields()
      this.emptyJsonKey('onlineUploadParams')
      await this.getFilePath()
      await this.queryOnlinePackages()
      await this.getbaselinePkg('onlineUploadParams')
      this.onlineModal = true
    },
    async getFilePath () {
      const { status, data } = await getFilePath(this.guid)
      if (status === 'OK') {
        this.onlineUploadParams.filterPath = data.artifact_path || ''
      }
    },
    // onlineUploadParams: {
    //   filterPath: '后台提供接口',
    emptyJsonKey (objName) {
      let obj = this[objName]
      Object.keys(obj).forEach(key => {
        if (key !== 'package_type') {
          obj[key] = ''
        }
      })
      return obj
    },
    // 获取在线包列表
    async queryOnlinePackages () {
      this.onlinePackages = []
      const { status, data } = await queryArtifactsList(this.guid, { filters: [], paging: false })
      if (status === 'OK') {
        this.onlinePackages = data
      }
    },
    // 获取基线列表
    async getbaselinePkg (type) {
      this[type].baseline_package = ''
      this.baselinePackageOptions = []
      let { status, data } = await queryPackages(this.guid, {
        resultColumns: ['guid', 'name', 'package_type', 'diff_conf_file', 'start_file_path', 'stop_file_path', 'deploy_file_path', 'is_decompression', 'db_diff_conf_file', 'db_upgrade_directory', 'db_rollback_directory', 'db_deploy_file_path', 'db_upgrade_file_path', 'db_rollback_file_path'],
        sorting: {
          asc: false,
          field: 'upload_time'
        },
        filters: [
          {
            name: 'package_type',
            operator: 'eq',
            value: this[type].package_type
          }
        ],
        paging: true,
        pageable: {
          pageSize: 1000,
          startIndex: 0
        }
      })
      if (status === 'OK') {
        this.baselinePackageOptions = data.contents.map(item => {
          return {
            ...item
          }
        })
      }
    },
    // 确认上传
    confirmOnlineUpload () {
      this.$refs['onlineUploadRuleValidateRef'].validate(async valid => {
        if (valid) {
          this.loading = true
          this.$Notice.success({
            title: this.$t('art_success'),
            desc: this.$t('art_need_time')
          })
          const { status } = await uploadArtifact(this.guid, this.onlineUploadParams.downloadUrl, this.onlineUploadParams.baseline_package, this.onlineUploadParams.package_type)
          if (status === 'OK') {
            this.loading = false
            this.onlineModal = false
            this.$emit('refreshTable', this.onlineUploadParams.package_type)
          } else {
            this.loading = false
          }
        }
      })
    },
    handleUpload (file) {
      this.removeFormDataKey('file')
      this.localUploadParams.fileName = file.name
      this.localUploadParams.size = this.formatFileSize(file.size)
      this.formData.append('file', file)
      return false
    },
    formatFileSize (bytes) {
      if (bytes === 0) return '0 Bytes'
      const units = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
      const unitIndex = Math.floor(Math.log(bytes) / Math.log(1024))
      const size = (bytes / Math.pow(1024, unitIndex)).toFixed(2)
      return `${size} ${units[unitIndex]}`
    },
    removeFormDataKey (keyToRemove) {
      let newFormData = new FormData()
      for (let [key, value] of this.formData.entries()) {
        if (key !== keyToRemove) {
          newFormData.append(key, value)
        }
      }
      this.formData = newFormData
    },
    // 本地上传
    async confirmLocalUpload () {
      this.removeFormDataKey('baseline_package')
      this.removeFormDataKey('package_type')
      this.formData.append('baseline_package', this.localUploadParams.baseline_package || '')
      this.formData.append('package_type', this.localUploadParams.package_type)
      this.loading = true
      this.$Notice.success({
        title: this.$t('art_success'),
        desc: this.$t('art_need_time')
      })
      const { status } = await uploadLocalArtifact(this.guid, this.formData)
      if (status === 'OK') {
        this.loading = false
        this.localModal = false
        this.$emit('refreshTable', this.localUploadParams.package_type)
      } else {
        this.loading = false
      }
    },
    fullscreenChange () {
      this.isfullscreen = !this.isfullscreen
    }
  },
  components: {}
}
</script>

<style scoped lang="scss">
.custom-modal-header {
  line-height: 20px;
  font-size: 16px;
  color: #17233d;
  font-weight: 500;
  .fullscreen-icon {
    float: right;
    margin-right: 28px;
    font-size: 18px;
    cursor: pointer;
  }
}
</style>
