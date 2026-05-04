<template>
  <view class="container">
    <view class="header">
      <text class="title">🐾 校园流浪猫档案</text>
    </view>

    <!-- 猫咪列表渲染区 -->
    <view class="cat-list">
      <view class="cat-card" v-for="cat in catList" :key="cat.id">
        <view class="cat-info">
          <text class="cat-name">{{ cat.name }} ({{ cat.gender }})</text>
          <text class="cat-tag">{{ cat.color }}</text>
          <text class="cat-location">📍 {{ cat.location }}</text>
        </view>
        <view class="cat-status">
          <!-- 根据绝育状态显示不同颜色 -->
          <text :class="['status-badge', cat.is_neutered ? 'safe' : 'warn']">
            {{ cat.is_neutered ? '已绝育(剪耳)' : '待绝育' }}
          </text>
          <text class="health-text">健康状况: {{ cat.health_status }}</text>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';

// 响应式变量，用于存放从后端获取的猫咪数据
const catList = ref([]);

// 获取数据的函数
const fetchCats = () => {
  uni.request({
    url: 'http://127.0.0.1:5000/api/cats', // 我们刚才写的 Flask 接口
    method: 'GET',
    success: (res) => {
      if (res.data && res.data.status === 'success') {
        catList.value = res.data.data;
        console.log('数据获取成功:', catList.value);
      }
    },
    fail: (err) => {
      console.error('获取猫咪数据失败:', err);
      uni.showToast({ title: '网络请求失败', icon: 'none' });
    }
  });
};

// 页面加载时执行
onMounted(() => {
  fetchCats();
});
</script>

<style scoped>
/* 简单的页面样式 (你也可以不用管，交给我来设计) */
.container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}
.header {
  margin-bottom: 20px;
  text-align: center;
}
.title {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}
.cat-card {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}
.cat-name {
  font-size: 18px;
  font-weight: bold;
  display: block;
  margin-bottom: 6px;
}
.cat-tag {
  background-color: #ffe4b5;
  color: #ff8c00;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 8px;
}
.cat-location {
  font-size: 12px;
  color: #666;
}
.cat-status {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #eee;
}
.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: white;
  margin-right: 10px;
}
.safe { background-color: #67c23a; }
.warn { background-color: #e6a23c; }
.health-text {
  font-size: 12px;
  color: #666;
}
</style>