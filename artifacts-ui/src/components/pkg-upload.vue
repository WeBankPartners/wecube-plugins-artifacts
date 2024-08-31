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
      <Form :label-width="80" ref="onlineUploadRuleValidateRef" :model="onlineUploadParams" :rules="onlineUploadRuleValidate">
        <FormItem :label="$t('filterPath')">
          <span style="vertical-align: middle;">{{ onlineUploadParams.filterPath }}</span>
        </FormItem>
        <FormItem :label="$t('art_package')" prop="downloadUrl">
          <Select filterable clearable v-model="onlineUploadParams.downloadUrl">
            <Option v-for="conf in onlinePackages" :value="conf.downloadUrl" :label="conf.name" :key="conf.downloadUrl">
              <span>{{ conf.name }}</span>
              <!-- <span style="float:right;color:#ccc">{{ dayjs(conf.lastModified).format('YYYY-MM-DD HH:mm:ss') }}</span> -->
            </Option>
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
        <Button type="primary" @click="confirmOnlineUpload">{{ $t('art_upload') }}</Button>
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
      <Form :label-width="80">
        <FormItem :label="$t('art_package')">
          <Upload action="" :before-upload="handleUpload">
            <Button icon="ios-cloud-upload-outline">{{ $t('artifacts_upload_new_package') }}</Button>
          </Upload>
          <span>{{ localUploadParams.fileName }}</span>
        </FormItem>
        <FormItem :label="$t('baseline_package')">
          <Select clearable filterable :placeholder="$t('baseline_package')" v-model="localUploadParams.baseline_package">
            <Option v-for="conf in baselinePackageOptions" :value="conf.guid" :key="conf.name">{{ conf.name }}</Option>
          </Select>
        </FormItem>
      </Form>
      <div slot="footer">
        <Button @click="localModal = false">{{ $t('artifacts_cancel') }}</Button>
        <Button type="primary" @click="confirmLocalUpload">{{ $t('art_upload') }}</Button>
      </div>
    </Modal>
  </div>
</template>

<script>
// import dayjs from 'dayjs'
import { queryArtifactsList, queryPackages, uploadArtifact, uploadLocalArtifact, getFilePath } from '@/api/server.js'
export default {
  name: '',
  data () {
    return {
      isfullscreen: false,
      guid: '', // 当前单元
      uploadType: '', // uploadType: 'local' | 'online'
      onlineModal: false,
      onlineUploadParams: {
        filterPath: '后台提供接口',
        downloadUrl: '',
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
        baseline_package: ''
      },
      formData: null
    }
  },
  watch: {},
  props: [],
  methods: {
    openUploadDialog (uploadType, guid) {
      this.isfullscreen = false
      this.uploadType = uploadType
      this.guid = guid
      if (uploadType === 'online') {
        this.onlineUpload()
      } else {
        this.localUpload()
      }
    },
    async localUpload () {
      this.emptyJsonKey('localUploadParams')
      await this.getbaselinePkg()
      this.localModal = true
    },
    // 在线包上传
    async onlineUpload () {
      this.$refs['onlineUploadRuleValidateRef'].resetFields()
      this.emptyJsonKey('onlineUploadParams')
      await this.getFilePath()
      await this.queryOnlinePackages()
      await this.getbaselinePkg()
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
        obj[key] = ''
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
    async getbaselinePkg () {
      this.baselinePackageOptions = []
      let { status, data } = await queryPackages(this.guid, {
        resultColumns: ['guid', 'name', 'package_type', 'diff_conf_file', 'start_file_path', 'stop_file_path', 'deploy_file_path', 'is_decompression', 'db_diff_conf_file', 'db_upgrade_directory', 'db_rollback_directory', 'db_deploy_file_path', 'db_upgrade_file_path', 'db_rollback_file_path'],
        sorting: {
          asc: false,
          field: 'upload_time'
        },
        filters: [],
        paging: true,
        pageable: {
          pageSize: 100,
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
          const { status } = await uploadArtifact(this.guid, this.onlineUploadParams.downloadUrl, this.onlineUploadParams.baseline_package)
          if (status === 'OK') {
            this.$Notice.success({
              title: this.$t('art_success'),
              desc: this.$t('art_need_time')
            })
            this.onlineModal = false
            this.$emit('refreshTable')
          }
        }
      })
    },
    handleUpload (file) {
      console.log(file)
      this.localUploadParams.fileName = file.name
      this.formData = new FormData()
      this.formData.append('file', file)
    },
    // 本地上传
    async confirmLocalUpload () {
      this.formData.append('baseline_package', this.localUploadParams.baseline_package)
      const { status } = await uploadLocalArtifact(this.guid, this.formData)
      if (status === 'OK') {
        this.$Notice.success({
          title: this.$t('art_success'),
          desc: this.$t('art_need_time')
        })
        this.localModal = false
        this.$emit('refreshTable')
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
