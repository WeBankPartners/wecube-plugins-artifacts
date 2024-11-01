<template>
  <div class="art-title">
    <div class="art-header">
      <div class="title">
        {{ title }}
        <span class="underline"></span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: '',
  data () {
    return {}
  },
  props: ['title'],
  methods: {},
  components: {}
}
</script>

<style scoped lang="scss">
.art-title {
  margin-bottom: 16px;
  .art-header {
    display: -webkit-box;
    display: -ms-flexbox;
    display: flex;
    -webkit-box-align: center;
    -ms-flex-align: center;
    align-items: center;
    .title {
      font-size: 16px;
      font-weight: 700;
      color: #515a6e;
      margin: 0 6px;
      .underline {
        display: block;
        margin-top: -12px;
        margin-left: -8px;
        width: 100%;
        padding: 0 8px;
        height: 12px;
        border-radius: 12px;
        background-color: #c6eafe;
        -webkit-box-sizing: content-box;
        box-sizing: content-box;
      }
    }
  }
}
</style>
