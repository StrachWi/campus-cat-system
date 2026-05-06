<template>
  <view class="admin-container">
    <!-- 顶部标题区 (体现内部审查性质) -->
    <view class="admin-header">
      <text class="title">📋 学术审查与内部管理端</text>
      <text class="subtitle">待审核的系统录入测试数据</text>
    </view>

    <!-- 空状态：如果没有待审核的数据 -->
    <view class="empty-state" v-if="pendingCats.length === 0">
      <text class="empty-icon">☕</text>
      <text class="empty-text">当前无待审核的录入数据，老师辛苦了！</text>
    </view>

    <!-- 待审核列表容器开始 -->
    <view class="cat-list" v-else>
      <!-- 列表项：每一只待审核的猫咪 -->
      <view class="review-card" v-for="cat in pendingCats" :key="cat.id">
        <view class="cat-info-row">
          <image class="cat-avatar" :src="cat.avatar_url" mode="aspectFill"></image>
          <view class="cat-details">
            <view class="name-line">
              <text class="cat-name">{{ cat.name }}</text>
              <text class="gender-tag">{{ cat.gender }}</text>
            </view>
            <text class="cat-desc">📍 地点：{{ cat.location }}</text>
            <text class="cat-desc">📝 性格：{{ cat.character_desc }}</text>
          </view>
        </view>

        <!-- 操作按钮区 -->
        <view class="action-row">
          <button class="btn reject-btn" @click="handleReview(cat.id, 'reject')">打回删除</button>
          <button class="btn pass-btn" @click="handleReview(cat.id, 'pass')">审核通过</button>
        </view>
      </view>
      
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';

const pendingCats = ref([]);
// 向后端请求待审核(pending)的猫咪数据
const fetchPendingCats = () => {
  uni.request({
    url: 'http://192.168.43.202:5000/api/admin/pending_cats', 
    method: 'GET',
    success: (res) => {
      if (res.data && res.data.status === 'success') {
        let data = res.data.data;
        data.forEach(cat => {
          if (!cat.avatar_url) {
             // 默认占位图
            cat.avatar_url = 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=200&h=200&fit=crop';
          }
        });
        pendingCats.value = data;
      }
    }
  });
};

// 页面每次显示时，自动执行拉取
onShow(() => {
  fetchPendingCats();
});
// 处理审核操作：通过(pass) 或 打回(reject)
const handleReview = (id, action) => {
  const actionText = action === 'pass' ? '通过' : '打回删除';
  
  uni.showModal({
    title: '审核确认',
    content: `确定要${actionText}这条录入数据吗？`,
    success: (res) => {
      if (res.confirm) {
        uni.request({
          url: 'http://192.168.43.202:5000/api/admin/review_cat',
          method: 'POST',
          data: { cat_id: id, action: action },
          success: (reviewRes) => {
            if (reviewRes.data?.status === 'success') {
              uni.showToast({ title: `已${actionText}`, icon: 'success' });
              // 操作成功后重新拉取列表，该猫咪会自动从列表中消失
              fetchPendingCats();
            } else {
              uni.showToast({ title: reviewRes.data?.message || '操作失败', icon: 'none' });
            }
          }
        });
      }
    }
  });
};
</script>
<style scoped>
.admin-container { min-height: 100vh; background-color: #f5f7fa; padding-bottom: 30px; }
.admin-header { background: linear-gradient(135deg, #4facfe, #00f2fe); padding: 50px 20px 25px; border-radius: 0 0 24px 24px; margin-bottom: 15px; }
.title { display: block; font-size: 20px; font-weight: bold; color: #fff; margin-bottom: 5px; }
.subtitle { font-size: 13px; color: rgba(255,255,255,0.8); }

.empty-state { display: flex; flex-direction: column; align-items: center; padding-top: 100px; }
.empty-icon { font-size: 50px; margin-bottom: 15px; }
.empty-text { color: #999; font-size: 14px; }

.cat-list { padding: 0 15px; }
.review-card { background: #fff; border-radius: 16px; padding: 16px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }
.cat-info-row { display: flex; margin-bottom: 15px; }
.cat-avatar { width: 70px; height: 70px; border-radius: 10px; margin-right: 15px; background-color: #eee; }
.cat-details { flex: 1; display: flex; flex-direction: column; justify-content: flex-start;}
.name-line { display: flex; align-items: center; margin-bottom: 6px; }
.cat-name { font-size: 18px; font-weight: bold; color: #333; margin-right: 8px; }
.gender-tag { font-size: 12px; background: #f0f2f5; color: #666; padding: 2px 6px; border-radius: 4px; }
.cat-desc { font-size: 13px; color: #666; margin-bottom: 4px; }

.action-row { display: flex; justify-content: flex-end; gap: 12px; border-top: 1px solid #f9f9f9; padding-top: 12px; }
.btn { margin: 0; font-size: 13px; border-radius: 20px; padding: 0 20px; height: 32px; line-height: 32px; }
.reject-btn { background-color: #fff; color: #f56c6c; border: 1px solid #f56c6c; }
.pass-btn { background-color: #4facfe; color: #fff; }
</style>