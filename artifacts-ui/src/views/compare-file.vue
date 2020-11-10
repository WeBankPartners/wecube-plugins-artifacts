<template>
  <div class="compare-show-container">
    <div v-if="originContent" class="container-item">
      <Card>
        <p slot="title">{{ $t('original_content') }}：</p>
        <p v-html="originContent" :style="contentSty"></p>
      </Card>
    </div>
    <div v-if="newContent" class="container-item">
      <Card>
        <p slot="title">{{ $t('new_content') }}：</p>
        <p v-html="newContent" :style="contentSty"></p>
      </Card>
    </div>
    <div v-if="originContent && newContent" class="container-item">
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
    compareFile (originContent, newContent) {
      this.compareResult = ''
      this.originContent = originContent.replace(/\n/g, '<br>')
      this.newContent = newContent.replace(/\n/g, '<br>')
      const diff = Diff.diffChars(this.originContent, this.newContent)
      diff.forEach(part => {
        // green for additions, red for deletions
        // grey for common parts
        const color = part.added ? 'green' : part.removed ? 'red' : 'grey'
        part.color = color
      })
      diff.forEach(item => {
        this.compareResult += `<span style='color:${item.color}'>${item.value}<span>`
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
