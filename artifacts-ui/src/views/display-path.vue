<template>
  <span>
    <div v-if="file.comparisonResult === 'new'" class="baseline-cmp-new">[{{ file.comparisonResult }}]</div>
    <div v-if="file.comparisonResult === 'same'" class="baseline-cmp-same">[{{ file.comparisonResult }}]</div>
    <div v-if="file.comparisonResult === 'changed'" class="baseline-cmp-changed">[{{ file.comparisonResult }}]</div>
    <div v-if="file.comparisonResult === 'deleted'" class="baseline-cmp-deleted">[{{ file.comparisonResult }}]</div>
    <div v-if="[null, ''].includes(file.comparisonResult)" class="baseline-cmp-deleted"></div>
    <Icon v-if="canBeMoved" type="ios-move" size="18" style="cursor: move" />
  </span>
</template>

<script>
export default {
  name: '',
  data () {
    return {}
  },
  props: ['packageInput', 'file', 'canBeMoved'],
  methods: {},
  components: {}
}
</script>

<style scoped lang="scss">
.common-position {
  width: 60px;
  margin: 0 4px;
  display: inline-block;
}
.baseline-cmp-new {
  color: #19be6b;
  @extend .common-position;
}
.baseline-cmp-same {
  @extend .common-position;
}
.baseline-cmp-changed {
  color: #2d8cf0;
  @extend .common-position;
}
.baseline-cmp-deleted {
  color: #ed4014;
  @extend .common-position;
}
</style>
