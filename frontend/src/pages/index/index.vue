<template>
  <view class="container">
    <view class="top-action-bar">
      <view class="discover-btn" @click="goToDiscover"><text>📷 发现新猫咪</text></view>
      <view class="filter-area" @click="showFilter = true">
        <text class="filter-text">筛选待喂养 ▾</text>
      </view>
    </view>
    
    <view class="cat-list">
      <view class="cat-card" v-for="cat in displayCatList" :key="cat.id">
        <view class="card-header" @click="goToDetail(cat.id)">
          <image class="cat-avatar" :src="formatImageUrl(cat.avatar_url)" mode="aspectFill"></image>
          <view class="cat-info">
            <view class="name-row">
              <text class="name">{{ cat.name }}</text>
              <text :class="['tag', cat.is_neutered ? 'tag-safe' : 'tag-warn']">{{ cat.is_neutered ? '已绝育' : '未绝育' }}</text>
            </view>
            <text class="location">📍 {{ cat.location }}</text>
          </view>
        </view>
        
        <view class="feed-progress-box">
          <text class="progress-title">今日干饭排班：</text>
          <view class="progress-bar">
            <view :class="['segment', cat.feed_status?.morning ? 'fed' : 'hungry']"><text>早</text></view>
            <view :class="['segment', cat.feed_status?.noon ? 'fed' : 'hungry']"><text>中</text></view>
            <view :class="['segment', cat.feed_status?.evening ? 'fed' : 'hungry']"><text>晚</text></view>
          </view>
        </view>
      </view>
    </view>

    <!-- 弹窗部分 -->
    <view class="modal-mask" v-if="showFilter" @click="showFilter = false">
      <view class="modal-content" @click.stop>
        <view class="modal-header">
          <text class="modal-title">查看哪个时段还需要喂猫？</text>
          <text class="close-btn" @click="showFilter = false">✕</text>
        </view>
        <view class="meal-options">
          <view v-for="meal in ['早', '中', '晚']" :key="meal" :class="['meal-btn', selectedMeals.includes(meal) ? 'meal-active' : '']" @click="toggleMeal(meal)">{{ meal }}餐</view>
        </view>
        <view class="modal-footer">
          <button class="reset-btn" @click="selectedMeals = []">重置全部</button>
          <button class="confirm-btn" @click="showFilter = false">确认</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { config } from '@/config.js';

const catList = ref([]);
const showFilter = ref(false);
const selectedMeals = ref([]);

const goToDiscover = () => { uni.navigateTo({ url: '/pages/discover/discover' }); };

const formatImageUrl = (url) => {
  if (!url) {
    return 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=200&h=200&fit=crop';
  }
  
  let newUrl = url;
  
  if (newUrl.includes('192.168.43.202')) {
    newUrl = newUrl.replace(/http:\/\/192\.168\.43\.202:\d+/g, config.baseUrl);
  }
  
  if (newUrl.includes('/api/uploads/')) {
    newUrl = newUrl.replace('/api/uploads/', '/static/uploads/');
  }
  
  if (!newUrl.startsWith('http')) {
    const prefix = newUrl.startsWith('/') ? '' : '/';
    newUrl = config.baseUrl + prefix + newUrl;
  }
  
  return newUrl;
};

const fetchCats = () => {
  uni.request({
    url: `${config.baseUrl}/api/cats`,
    method: 'GET',
    success: (res) => {
      if (res.data?.status === 'success') {
        let data = res.data.data;
        data.forEach((cat) => {
          if (!cat.avatar_url) {
            cat.avatar_url = 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=200&h=200&fit=crop';
          } else if (!cat.avatar_url.startsWith('http')) {
            cat.avatar_url = config.baseUrl + cat.avatar_url;
          }
        });
        catList.value = data;
      }
    }
  });
};

const toggleMeal = (meal) => {
  const index = selectedMeals.value.indexOf(meal);
  if (index > -1) selectedMeals.value.splice(index, 1);
  else selectedMeals.value.push(meal);
};

const displayCatList = computed(() => {
  if (selectedMeals.value.length === 0) return catList.value;
  return catList.value.filter(cat => {
    let match = false;
    if (selectedMeals.value.includes('早') && !cat.feed_status?.morning) match = true;
    if (selectedMeals.value.includes('中') && !cat.feed_status?.noon) match = true;
    if (selectedMeals.value.includes('晚') && !cat.feed_status?.evening) match = true;
    return match;
  });
});

const goToDetail = (id) => { uni.navigateTo({ url: `/pages/detail/detail?id=${id}` }); };

onShow(() => { fetchCats(); });
</script>

<style scoped>
.container { min-height: 100vh; background-color: #f5f7fa; padding: 12px; }
.top-action-bar { display: flex; justify-content: space-between; align-items: center; background-color: #fff; padding: 12px 16px; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.discover-btn { background-color: #fff3e0; color: #ff8c00; padding: 6px 12px; border-radius: 20px; font-weight: bold; font-size: 14px; display: flex; align-items: center; }
.filter-area { display: flex; align-items: center; background-color: #f5f5f5; padding: 6px 12px; border-radius: 16px; }
.filter-text { font-size: 13px; color: #666; }
.cat-card { background-color: #fff; border-radius: 16px; padding: 16px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); }
.card-header { display: flex; align-items: center; margin-bottom: 16px; }
.cat-avatar { width: 60px; height: 60px; border-radius: 50%; margin-right: 12px; background-color: #eee; }
.cat-info { flex: 1; }
.name-row { display: flex; align-items: center; margin-bottom: 6px; }
.name { font-size: 18px; font-weight: bold; color: #333; margin-right: 8px; }
.tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; }
.tag-safe { background-color: #e1f3d8; color: #67c23a; }
.tag-warn { background-color: #fde2e2; color: #f56c6c; }
.location { font-size: 12px; color: #999; }
.feed-progress-box { background-color: #fafafa; padding: 10px; border-radius: 8px; }
.progress-title { font-size: 12px; color: #666; margin-bottom: 8px; display: block; }
.progress-bar { display: flex; gap: 8px; }
.segment { flex: 1; height: 24px; border-radius: 12px; display: flex; justify-content: center; align-items: center; font-size: 11px; font-weight: bold; }
.fed { background-color: #67c23a; color: white; }
.hungry { background-color: #fde2e2; color: #f56c6c; }
.modal-mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); z-index: 999; display: flex; align-items: flex-end; }
.modal-content { background-color: #fff; width: 100%; border-radius: 20px 20px 0 0; padding: 20px; box-sizing: border-box; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.modal-title { font-size: 16px; font-weight: bold; color: #333; }
.close-btn { font-size: 20px; color: #999; padding: 0 10px; }
.meal-options { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 30px; }
.meal-btn { flex: 1; text-align: center; padding: 12px 0; border-radius: 8px; background-color: #f5f5f5; color: #666; font-size: 15px; border: 1px solid transparent; }
.meal-active { background-color: #fff3e0; color: #ff8c00; border-color: #ff8c00; font-weight: bold; }
.modal-footer { display: flex; gap: 16px; }
.reset-btn { flex: 1; background-color: #f5f5f5; color: #666; font-size: 15px; border-radius: 24px; }
.confirm-btn { flex: 2; background-color: #ff8c00; color: #fff; font-size: 15px; border-radius: 24px; }
</style>