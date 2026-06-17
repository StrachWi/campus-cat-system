<template>
  <view class="container">
    <view class="top-action-bar">
      <view class="discover-btn" @click="goToDiscover"><text>📷 发现新猫咪</text></view>
      <view class="filter-area" @click="showFilter = true">
        <text class="filter-text">筛选待喂养 ▾</text>
      </view>
      <view class="filter-area" @click="showPicker = true">
        <text class="filter-text">筛选毛色或性别 ▾</text>
      </view>
    </view>

    <view class="top-action-bar2">
      <view class="search-area">
        <button class="search-box" @click="clean">重置选项</button>
        <input type="search" class="input-box" v-model="key" placeholder="输入名字或地点"/>
        <button class="search-box" v-if="key" @click="key = ''">清空</button>
      </view>
    </view>

    <!-- 视图切换 -->
    <view class="view-switch">
      <view :class="['switch-tab', viewMode === 'cats' ? 'switch-active' : '']" @click="viewMode = 'cats'">🐱 猫咪列表</view>
      <view :class="['switch-tab', viewMode === 'schedule' ? 'switch-active' : '']" @click="viewMode = 'schedule'; page=1; fetchSchedule()">📋 历史排班</view>
    </view>

    <!-- 猫咪列表视图 -->
    <view v-show="viewMode === 'cats'" class="cat-list">
      <view class="cat-card" v-for="cat in displaylist" :key="cat.id">
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
            <view :class="['segment', getSegmentClass('morning', cat)]"><text>早</text></view>
            <view :class="['segment', getSegmentClass('noon', cat)]"><text>中</text></view>
            <view :class="['segment', getSegmentClass('evening', cat)]"><text>晚</text></view>
          </view>
        </view>
      </view>
    </view>

    <!-- 历史排班视图 -->
    <view v-show="viewMode === 'schedule'" class="schedule-list">
      <view v-if="scheduleList.length === 0" class="empty-state">
        <text>暂无历史喂养记录</text>
      </view>
      <view class="schedule-card" v-for="item in scheduleList" :key="item.cat_id + '_' + item.date">
        <view class="schedule-header">
          <image v-if="item.cat_avatar" class="schedule-avatar" :src="formatImageUrl(item.cat_avatar)" mode="aspectFill"></image>
          <view class="schedule-info">
            <text class="schedule-name">{{ item.cat_name }}</text>
            <text class="schedule-date">📅 {{ item.date }}</text>
          </view>
        </view>
        <view class="schedule-meals">
          <view v-for="meal in ['morning','noon','evening']" :key="meal" :class="['schedule-meal', getScheduleMealClass(meal, item)]">
            <text class="meal-label">{{ mealNameMap[meal] }}</text>
            <text class="meal-claimer">{{ getScheduleMealText(meal, item) }}</text>
          </view>
        </view>
      </view>
      <view v-if="scheduleList.length > 0" class="pagination-bar">
        <button class="page-btn" :disabled="page <= 1" @click="prevPage">上一页</button>
        <text class="page-num">{{ page }} / {{ totalPages || 1 }}</text>
        <button class="page-btn" :disabled="page >= totalPages" @click="nextPage">下一页</button>
      </view>
    </view>

    <!-- 筛选弹窗 -->
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

    <view class="modal-mask" v-if="showPicker" @click="showPicker=false">
      <view class="modal-content" @click.stop>
        <view class="modal-header">
          <text class="modal-title">选择毛色或性别</text>
          <text class="close-btn" @click="showPicker = false">✕</text>
        </view>
        <text>选择毛色</text>
        <view class="meal-options">
          <view v-for="rgb in colorlist" :key="rgb" :class="['meal-btn', colors.includes(rgb) ? 'meal-active' : '']" @click="toggleColor(rgb)">{{ rgb }}色</view>
        </view>
        <text>选择性别</text>
        <view class="meal-options">
          <view v-for="g in genderlist" :key="g" :class="['meal-btn', genders.includes(g) ? 'meal-active' : '']" @click="toggleGender(g)">{{ g }}</view>
        </view>
        <view class="modal-footer">
          <button class="reset-btn" @click="colors=[]">重置全部</button>
          <button class="confirm-btn" @click="showPicker = false">确认</button>
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
const showPicker = ref(false);
const selectedMeals = ref([]);
const colors = ref([]);
const key = ref('');
const genders = ref([]);
const viewMode = ref('cats');
const scheduleList = ref([]);
const page = ref(1);
const totalPages = ref(1);
const mealNameMap = { morning: '早餐', noon: '午餐', evening: '晚餐' };

const clean = () => {
  colors.value = [];
  selectedMeals.value = [];
  genders.value = [];
  key.value = '';
};

const goToDiscover = () => { uni.navigateTo({ url: '/pages/discover/discover' }); };

const formatImageUrl = (url) => {
  if (!url) return 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=200&h=200&fit=crop';
  let newUrl = url;
  if (newUrl.includes('192.168.43.202')) newUrl = newUrl.replace(/http:\/\/192\.168\.43\.202:\d+/g, config.baseUrl);
  if (newUrl.includes('/api/uploads/')) newUrl = newUrl.replace('/api/uploads/', '/static/uploads/');
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
          if (!cat.avatar_url) cat.avatar_url = 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=200&h=200&fit=crop';
          else if (!cat.avatar_url.startsWith('http')) cat.avatar_url = config.baseUrl + cat.avatar_url;
        });
        catList.value = data;
      }
    },
  });
};

const getSegmentClass = (meal, cat) => {
  const claimer = cat.feed_status?.[meal];
  if (!claimer) return 'hungry';
  // Check if claimer is admin — we check if claimer is a user_id that looks like admin
  // No good way from frontend; just show as fed (green) for now; admin info comes from backend
  return 'fed';
};

const fetchSchedule = () => {
  uni.request({
    url: `${config.baseUrl}/api/cats/feeding/schedule?page=${page.value}&limit=10`,
    method: 'GET',
    success: (res) => {
      if (res.data?.status === 'success') {
        scheduleList.value = res.data.data || [];
        totalPages.value = Math.ceil((res.data.pagination?.total || 0) / 10) || 1;
      }
    },
  });
};

const prevPage = () => { if (page.value > 1) { page.value--; fetchSchedule(); } };
const nextPage = () => { if (page.value < totalPages.value) { page.value++; fetchSchedule(); } };

const getScheduleMealClass = (meal, item) => {
  const mealData = item[meal];
  if (!mealData) return 'meal-none';
  const claimStatus = mealData.claimer?.status || 'none';
  if (claimStatus === 'admin') return 'meal-admin';
  if (claimStatus === 'claimed') return 'meal-claimed';
  return 'meal-none';
};

const getScheduleMealText = (meal, item) => {
  const mealData = item[meal];
  if (!mealData) return '无人认领';
  const claimStatus = mealData.claimer?.status || 'none';
  if (claimStatus === 'none') return '无人认领';
  if (claimStatus === 'admin') return '管理员认领';
  return mealData.claimer?.username || '已认领';
};

const toggleMeal = (meal) => {
  const index = selectedMeals.value.indexOf(meal);
  if (index > -1) selectedMeals.value.splice(index, 1);
  else selectedMeals.value.push(meal);
};
const toggleColor = (color) => {
  const index = colors.value.indexOf(color);
  if (index > -1) colors.value.splice(index, 1);
  else colors.value.push(color);
};
const toggleGender = (gender) => {
  const index = genders.value.indexOf(gender);
  if (index > -1) genders.value.splice(index, 1);
  else genders.value.push(gender);
};

const displayCatList = computed(() => {
  if (selectedMeals.value.length === 0) return catList.value;
  return catList.value.filter((cat) => {
    let match = false;
    if (selectedMeals.value.includes('早') && !cat.feed_status?.morning) match = true;
    if (selectedMeals.value.includes('中') && !cat.feed_status?.noon) match = true;
    if (selectedMeals.value.includes('晚') && !cat.feed_status?.evening) match = true;
    return match;
  });
});
const finalList = computed(() => {
  return displayCatList.value.filter((cat) => {
    return (genders.value.includes(cat.gender) || genders.value.length === 0) && (colors.value.includes(cat.color) || colors.value.length === 0);
  });
});
const displaylist = computed(() => {
  if (!key.value) return finalList.value;
  return finalList.value.filter((cat) => cat.name.includes(key.value) || cat.location.includes(key.value));
});
const colorlist = computed(() => {
  if (!Array.isArray(catList.value)) return [];
  const temp = catList.value.map((item) => item.color);
  return [...new Set(temp)];
});
const genderlist = computed(() => {
  const temp = catList.value.map((item) => item.gender);
  return [...new Set(temp)];
});

const goToDetail = (id) => { uni.navigateTo({ url: `/pages/detail/detail?id=${id}` }); };

onShow(() => { fetchCats(); if (viewMode.value === 'schedule') fetchSchedule(); });
</script>

<style scoped>
.container { min-height: 100vh; background-color: #f5f7fa; padding: 12px; }
.search-area { display: flex; align-items: center; background-color: #ffffff; }
.input-box { background-color: #aaffff; font-size: 14px; color: #333; padding: 8px; border-style: inset; border-width: 2px; margin-left: 5px; }
.search-box { background-color: #ff5500; font-size: 12px; color: #000000; }
.top-action-bar { display: flex; justify-content: space-between; align-items: center; background-color: #fff; padding: 12px 16px; border-radius: 12px; margin-bottom: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.top-action-bar2 { display: flex; justify-content: space-between; align-items: center; background-color: #fff; padding: 12px 16px; border-radius: 12px; margin-bottom: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.discover-btn { background-color: #fff3e0; color: #ff8c00; padding: 6px 12px; border-radius: 20px; font-weight: bold; font-size: 14px; display: flex; align-items: center; }
.filter-area { display: flex; align-items: center; background-color: #f5f5f5; padding: 6px 12px; border-radius: 16px; }
.filter-text { font-size: 13px; color: #666; }

/* 视图切换 */
.view-switch { display: flex; gap: 10px; margin-bottom: 12px; }
.switch-tab { flex: 1; text-align: center; padding: 10px; border-radius: 10px; font-size: 14px; font-weight: 600; background: #fff; color: #666; box-shadow: 0 2px 6px rgba(0,0,0,0.04); }
.switch-active { background: linear-gradient(135deg, #ffb74d, #ff8c00); color: #fff; }

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

/* 历史排班 */
.schedule-list { display: flex; flex-direction: column; gap: 12px; }
.empty-state { text-align: center; padding: 60px 0; color: #999; font-size: 14px; }
.schedule-card { background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 3px 10px rgba(0,0,0,0.04); }
.schedule-header { display: flex; align-items: center; margin-bottom: 12px; }
.schedule-avatar { width: 48px; height: 48px; border-radius: 50%; margin-right: 10px; background: #eee; }
.schedule-info { flex: 1; }
.schedule-name { font-size: 16px; font-weight: 700; color: #333; display: block; }
.schedule-date { font-size: 12px; color: #999; }
.schedule-meals { display: flex; gap: 8px; }
.schedule-meal { flex: 1; text-align: center; padding: 10px 6px; border-radius: 10px; font-size: 12px; }
.meal-none { background: #f0f0f0; color: #999; }
.meal-admin { background: #e3f2fd; color: #1976d2; }
.meal-claimed { background: #e8f5e9; color: #388e3c; }
.meal-label { display: block; font-weight: 700; margin-bottom: 4px; }
.meal-claimer { display: block; font-size: 11px; }

.pagination-bar { display: flex; justify-content: center; align-items: center; gap: 16px; padding: 16px 0; }
.page-btn { padding: 8px 20px; border-radius: 20px; font-size: 13px; background: #fff; color: #ff8c00; border: 1px solid #ff8c00; }
.page-btn[disabled] { opacity: 0.4; }
.page-num { font-size: 14px; color: #666; }

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
