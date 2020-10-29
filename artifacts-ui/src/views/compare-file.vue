<template>
  <div class="compare-show-container">
    <div class="container-item">
      <Card>
        <p slot="title">旧内容：</p>
        <p v-html="originContent" class="content-sty"></p>
      </Card>
    </div>
    <div class="container-item">
      <Card>
        <p slot="title">新内容：</p>
        <p v-html="newContent" class="content-sty"></p>
      </Card>
    </div>
    <div class="container-item">
      <Card>
        <p slot="title">比对结果：</p>
        <p v-html="compareResult" class="content-sty"></p>
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
      originContent: 'beep boop12341234123333333333fdsgdsfgsafsadfasdfasdfasfasdfasdfasdfsadfasdfsdfg333333333333asdfasfasdfasdfasdfsadfasdfsdfg333333333333asdfasfasdfasdfasdfsadfasdfsdfg333333333333asdfasfasdfasdfasdfsadfasdfsdfg3333333333333333312341234',
      newContent: 'beep boob bla1233333333333333333333333331234h',
      compareResult: ''
    }
  },
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
.content-sty {
  word-break: break-all;
  height: 300px;
  overflow-y: auto;
}
</style>
