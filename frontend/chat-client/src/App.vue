<template>
  <div id="app">
    <NavBar />
    <div class="content">
      <router-view></router-view>
    </div>
        <Footer />
  </div>
</template>

<script>
import NavBar from './components/NavBar.vue'
import Footer from './components/Footer.vue'

export default {
  name: 'App',
  components: {
    NavBar,
    Footer
  }
}
</script>

<style>
#app {
  font-family: 'Noto Sans KR', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  display: block;
  flex-direction: column;
  margin: 0;
  padding: 0;
}

.content {
  flex: 1;
  padding-top: 60px;
  min-height: calc(100vh - 200px); /* footer 높이를 뺀 최소 높이 설정 */
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background-color: #f5f5f5;
  margin: 0;
  padding: 0;
  min-height: 100vh;
}
</style>
