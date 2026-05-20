<template>
  <view class="detail-container">
    <image :src="catInfo.avatar_url" mode="aspectFill"></image>

    <view class="info-section" v-if="catInfo.name">
      <view class="header-row">
        <text class="cat-name">{{ catInfo.name }}</text>
        <text class="gender-tag">{{ catInfo.gender === '公' ? '♂️' : '♀️' }}</text>
      </view>
      <view class="tag-row">
        <text class="tag">{{ catInfo.color }}</text>
        <text class="tag">{{ catInfo.is_neutered ? '已绝育' : '待绝育' }}</text>
        <text class="tag">健康：{{ catInfo.health_status }}</text>
      </view>
      
      <view class="desc-box">
        <text class="label">性格特征：</text>
        <text class="desc-content">{{ catInfo.character_desc || '暂无描述' }}</text>
      </view>
      
      <view class="location-box">
        <text class="label">常驻地点：</text>
        <text class="value">{{ catInfo.location }}</text>
      </view>
    </view>

    <view class="action-section" v-if="catInfo.feed_status">
      <view class="section-title">
        <text>🍱 今日喂养计划</text>
        <text class="tip">认领后请及时去投喂哦</text>
      </view>
      
      <view class="meal-plan">
        <view class="meal-item" v-for="meal in ['morning', 'noon', 'evening']" :key="meal">
          <view class="meal-info">
            <text class="meal-name">{{ mealNameMap[meal] }}</text>
            <text v-if="!catInfo.feed_status[meal]" class="meal-status status-pending">⌛ 待认领</text>
            <text v-else-if="catInfo.feed_status[meal] === myUserId" class="meal-status status-mine">✅ 我已认领</text>
            <text v-else class="meal-status status-others">🔒 已被其他爱心人士认领</text>
          </view>
          <button v-if="!catInfo.feed_status[meal]" class="action-btn claim-btn" @click="handleFeedAction(meal, 'claim')">认领</button>
          <button v-else-if="catInfo.feed_status[meal] === myUserId" class="action-btn cancel-btn" @click="handleFeedAction(meal, 'cancel')">取消</button>
          <button v-else class="action-btn disabled-btn" disabled>已被认领</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';

const catId = ref(null);
const catInfo = ref({});
const myUserId = ref('student_001');
const mealNameMap = { morning: '早餐', noon: '午餐', evening: '晚餐' };

const initUserId = () => {
  let uid = uni.getStorageSync('mock_user_id');
  if (!uid) {
    uid = 'user_' + Math.random().toString(36).substr(2, 9);
    uni.setStorageSync('mock_user_id', uid);
  }
  myUserId.value = uid;
};

onLoad((options) => {
  catId.value = options.id;
  initUserId();
});

onShow(() => {
  if (catId.value) fetchCatDetail();
});

const fetchCatDetail = () => {
  uni.request({
    url: 'http://192.168.43.202:5000/api/cats', 
    method: 'GET',
    success: (res) => {
      if(res.data.status === 'success') {
        const allCats = res.data.data;
        const targetCat = allCats.find(c => c.id == catId.value);
        if (targetCat) {
          if (targetCat.avatar_url && !targetCat.avatar_url.startsWith('http')) {
            targetCat.avatar_url = 'http://192.168.43.202:5000' + targetCat.avatar_url;
          }
          catInfo.value = targetCat;
        }
      }
    }
  });
};

const handleFeedAction = (meal, action) => {
  const isClaim = action === 'claim';
  const actionText = isClaim ? '认领' : '取消认领';

  uni.showModal({
    title: '操作确认',
    content: `确定要${actionText} ${catInfo.value.name} 的${mealNameMap[meal]}吗？`,
    success: (res) => {
      if (res.confirm) {
        uni.request({
          url: `http://192.168.43.202:5000/api/cats/${catId.value}/feed`,
          method: 'POST',
          data: { 
            meal: meal, 
            action: action,
            user_id: myUserId.value 
          },
          success: (res) => {
            if (res.data && res.data.status === 'success') {
              uni.showToast({ title: '操作成功', icon: 'success' });
              if (!catInfo.value.feed_status) catInfo.value.feed_status = {};
              catInfo.value.feed_status[meal] = res.data.new_claimer;
            } else {
              uni.showToast({ title: '服务器忙，请重试', icon: 'none' });
            }
          },
          fail: () => {
            uni.showToast({ title: '网络连接失败', icon: 'none' });
          }
        });
      }
    }
  });
};
</script>

<style scoped>
.detail-container { min-height: 100vh; background-color: #f8f9fa; padding-bottom: 50px; }
.main-image { width: 100%; height: 260px; background-color: #eee; }
.info-section { background-color: #fff; padding: 20px; border-radius: 0 0 24px 24px; margin-bottom: 12px; }
.header-row { display: flex; align-items: center; margin-bottom: 10px; }
.cat-name { font-size: 24px; font-weight: bold; color: #333; margin-right: 10px; }
.tag-row { display: flex; gap: 8px; margin-bottom: 15px; }
.tag { background-color: #f0f2f5; color: #666; padding: 4px 10px; border-radius: 6px; font-size: 12px; }

.desc-box { background: #fff9f0; padding: 12px; border-radius: 8px; margin-bottom: 12px; }
.label { color: #999; font-size: 14px; }
.desc-content { font-size: 14px; color: #ff8c00; font-style: italic; margin-left: 5px; }
.location-box { font-size: 14px; padding: 5px 0;}
.value { color: #333; font-weight: 500; margin-left: 5px;}

.action-section { background-color: #fff; padding: 20px; }
.section-title { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 20px; }
.section-title text:first-child { font-size: 18px; font-weight: bold; }
.tip { font-size: 11px; color: #ff8c00; }

.meal-plan { display: flex; flex-direction: column; gap: 15px; }
.meal-item { display: flex; justify-content: space-between; align-items: center; background-color: #fcfcfc; padding: 12px; border-radius: 12px; border: 1px solid #f5f5f5; }
.meal-name { font-size: 15px; font-weight: bold; display: block; margin-bottom: 4px; }
.meal-status { font-size: 12px; }

.status-pending { color: #909399; }
.status-mine { color: #67c23a; font-weight: bold;}
.status-others { color: #999; }

.action-btn { margin: 0; font-size: 13px; border-radius: 20px; padding: 0 20px; height: 32px; line-height: 32px;}
.claim-btn { background-color: #ff8c00; color: #fff; }
.cancel-btn { background-color: #fff; color: #ff8c00; border: 1px solid #ff8c00; }
.disabled-btn { background-color: #f5f5f5; color: #ccc; }
</style>
