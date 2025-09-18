<template>
  <div class="compare-show-container">
    <div v-if="fileStatus == 'changed'" class="container-item">
      <Card>
        <p slot="title">{{ $t('original_content') }}：</p>
        <p v-html="originContent" :style="contentSty"></p>
      </Card>
    </div>
    <div class="container-item">
      <Card>
        <p slot="title">{{ $t('new_content') }}：</p>
        <p v-html="newContent" :style="contentSty"></p>
      </Card>
    </div>
    <div v-if="fileStatus == 'changed'" class="container-item">
      <Card>
        <p slot="title">{{ $t('comparison_result') }}：</p>
        <p v-html="compareResult" :style="contentSty"></p>
      </Card>
    </div>
  </div>
</template>

<script>
const Diff = require('diff')
export default {
  name: '',
  data () {
    return {
      fileStatus: '',
      originContent: '',
      newContent: '',
      compareResult: '',
      contentSty: {
        wordBreak: 'break-all',
        height: this.fileContentHeight,
        overflowY: 'auto'
      }
    }
  },
  watch: {
    fileContentHeight: function (val) {
      this.contentSty.height = val
    }
  },
  props: ['fileContentHeight'],
  methods: {
    compareFile (originContent, newContent, fileStatus) {
      this.fileStatus = fileStatus
      this.compareResult = ''
      this.originContent = originContent.replace(/\n/g, '<br>')
      this.newContent = newContent.replace(/\n/g, '<br>')
      let diff = []
      if (originContent === '' && newContent !== '') {
        diff = [
          {
            added: true,
            color: 'green',
            count: 1234, // 模拟数据
            removed: undefined,
            value: this.newContent
          }
        ]
      } else {
        diff = Diff.diffChars(this.originContent, this.newContent)
      }
      diff.forEach(part => {
        // green for additions, red for deletions
        // grey for common parts
        const color = part.added ? 'green' : part.removed ? 'red' : 'grey'
        part.color = color
        this.compareResult += `<span style='color:${part.color}'>${part.value}<span>`
      })
    }
  },
  components: {}
}
</script>

<style scoped lang="scss">
.compare-show-container {
  display: flex;
}

.container-item {
  flex: 1;
  margin: 2px;
}
</style>
