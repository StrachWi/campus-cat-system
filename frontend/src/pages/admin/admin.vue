<template>
  <view class="admin-container">
    <view class="admin-header">
      <text class="title">教师/管理员控制台</text>
      <text class="subtitle">校园猫咪信息管控中心</text>
    </view>

    <!-- 顶部的两个选项卡 -->
    <view class="tabs-container">
      <view :class="['tab-item', currentTab === 'pending' ? 'active-tab' : '']" @click="currentTab = 'pending'">待审核</view>
      <view :class="['tab-item', currentTab === 'published' ? 'active-tab' : '']" @click="currentTab = 'published'">已发布(管理)</view>
    </view>

    <view class="cat-list">
      <!-- 列表A：待审核的猫咪 -->
      <view v-show="currentTab === 'pending'">
        <view v-if="pendingCats.length === 0" class="empty-state">
          <text class="empty-text">当前没有待审核的数据~</text>
        </view>
        <view class="review-card" v-for="cat in pendingCats" :key="cat.id">
          <view class="cat-info-row">
            <image class="cat-avatar" :src="formatImageUrl(cat.avatar_url)" mode="aspectFill"></image>
            <view class="cat-details">
              <text class="cat-name">{{ cat.name }}</text>
              <text class="cat-desc">📍 {{ cat.location }}</text>
              <text class="cat-desc">📝 {{ cat.character_desc }}</text>
            </view>
          </view>
          <view class="action-row">
            <button class="btn reject-btn" @click="handleReview(cat.id, 'reject')">打回删除</button>
            <button class="btn pass-btn" @click="handleReview(cat.id, 'pass')">审核通过</button>
          </view>
        </view>
      </view>

      <!-- 列表B：已发布的猫咪（具备删改功能） -->
      <view v-show="currentTab === 'published'">
        <view class="review-card" v-for="cat in publishedCats" :key="cat.id">
          <view class="cat-info-row">
            <image class="cat-avatar" :src="formatImageUrl(cat.avatar_url)" mode="aspectFill"></image>
            <view class="cat-details">
              <text class="cat-name">{{ cat.name }} (已发布)</text>
              <text class="cat-desc">📍 {{ cat.location }}</text>
              <text class="cat-desc">📝 {{ cat.character_desc }}</text>
            </view>
          </view>
          <view class="action-row">
            <button class="btn reject-btn" @click="handleDelete(cat.id)">下架并删除</button>
            <button class="btn pass-btn" @click="openEditModal(cat)">修改信息</button>
          </view>
        </view>
      </view>
    </view>

    <!-- 修改信息的隐藏弹窗 -->
    <view class="modal-mask" v-if="showEditModal">
      <view class="edit-modal">
        <text class="modal-title">修改基本信息</text>
        <input class="edit-input" v-model="editForm.name" placeholder="猫咪名字" />
        <input class="edit-input" v-model="editForm.location" placeholder="常出没地点" />
        <input class="edit-input" v-model="editForm.character_desc" placeholder="性格描述" />
        <view class="modal-footer">
          <button class="btn reject-btn" @click="showEditModal = false">取消</button>
          <button class="btn pass-btn" @click="submitEdit">保存</button>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { config } from '@/config.js';

const currentTab = ref('pending'); // 当前激活的Tab，默认待审核
const pendingCats = ref([]);
const publishedCats = ref([]);

// 弹窗相关变量
const showEditModal = ref(false);
const editForm = ref({ id: '', name: '', location: '', character_desc: '' });

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

// 1. 获取待审核数据
const fetchPendingCats = () => {
  uni.request({
    url: `${config.baseUrl}/api/admin/pending_cats`,
    success: (res) => { if (res.data?.status === 'success') pendingCats.value = res.data.data; }
  });
};

// 2. 获取已发布数据 (借用首页的接口)
const fetchPublishedCats = () => {
  uni.request({
    url: `${config.baseUrl}/api/cats`,
    success: (res) => { if (res.data?.status === 'success') publishedCats.value = res.data.data; }
  });
};

// 3. 处理审核 (旧功能)
const handleReview = (id, action) => {
  uni.request({
    url: `${config.baseUrl}/api/admin/review_cat`, method: 'POST', data: { cat_id: id, action: action },
    success: () => {
      uni.showToast({ title: '操作成功' });
      fetchPendingCats(); // 刷新待审核列表
      fetchPublishedCats(); // 刷新已发布列表
    }
  });
};

// 4. 删除已发布的猫咪 (新功能)
const handleDelete = (id) => {
  uni.showModal({
    title: '极其危险的操作', content: '确定要彻底删除这只猫咪的档案吗？',
    success: (res) => {
      if (res.confirm) {
        uni.request({
          url: `${config.baseUrl}/api/admin/delete_cat`, method: 'POST', data: { cat_id: id },
          success: () => { uni.showToast({ title: '已彻底删除' }); fetchPublishedCats(); }
        });
      }
    }
  });
};

// 5. 打开修改弹窗 (新功能)
const openEditModal = (cat) => {
  editForm.value = { id: cat.id, name: cat.name, location: cat.location, character_desc: cat.character_desc };
  showEditModal.value = true;
};

// 6. 提交修改并保存到数据库 (新功能)
const submitEdit = () => {
  uni.request({
    url: `${config.baseUrl}/api/admin/update_cat`, method: 'POST',
    data: { cat_id: editForm.value.id, name: editForm.value.name, location: editForm.value.location, character_desc: editForm.value.character_desc },
    success: () => {
      uni.showToast({ title: '信息已更新' });
      showEditModal.value = false;
      fetchPublishedCats(); // 刷新列表看最新效果
    }
  });
};

// 每次进入页面时，把两边的数据都拉取一次
onShow(() => { fetchPendingCats(); fetchPublishedCats(); });
</script>

<style scoped>
.admin-container { min-height: 100vh; background-color: #f5f7fa; padding-bottom: 30px; }
.admin-header { background: linear-gradient(135deg, #4facfe, #00f2fe); padding: 50px 20px 15px; }
.title { display: block; font-size: 20px; font-weight: bold; color: #fff; margin-bottom: 5px; }
.subtitle { font-size: 13px; color: rgba(255,255,255,0.8); }

/* 选项卡样式 */
.tabs-container { display: flex; background: #fff; padding: 0 20px; border-radius: 0 0 20px 20px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }
.tab-item { flex: 1; text-align: center; padding: 15px 0; font-size: 15px; color: #666; font-weight: bold; position: relative; }
.active-tab { color: #4facfe; }
.active-tab::after { content: ''; position: absolute; bottom: 0; left: 30%; width: 40%; height: 3px; background-color: #4facfe; border-radius: 3px; }

.empty-state { text-align: center; padding: 50px 0; }
.empty-text { color: #999; font-size: 14px; }

/* 列表卡片样式 */
.cat-list { padding: 0 15px; }
.review-card { background: #fff; border-radius: 16px; padding: 16px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }
.cat-info-row { display: flex; margin-bottom: 15px; }
.cat-avatar { width: 70px; height: 70px; border-radius: 10px; margin-right: 15px; background-color: #eee; }
.cat-details { flex: 1; display: flex; flex-direction: column; justify-content: space-around; }
.cat-name { font-size: 18px; font-weight: bold; color: #333; }
.cat-desc { font-size: 13px; color: #666; }

.action-row { display: flex; justify-content: flex-end; gap: 12px; border-top: 1px solid #f9f9f9; padding-top: 12px; }
.btn { margin: 0; font-size: 13px; border-radius: 20px; padding: 0 20px; height: 32px; line-height: 32px; }
.reject-btn { background-color: #fff; color: #f56c6c; border: 1px solid #f56c6c; }
.pass-btn { background-color: #4facfe; color: #fff; }

/* 弹窗样式 */
.modal-mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); z-index: 999; display: flex; align-items: center; justify-content: center; }
.edit-modal { background-color: #fff; width: 80%; border-radius: 16px; padding: 20px; }
.modal-title { display: block; font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 20px; }
.edit-input { background: #f5f7fa; border-radius: 8px; padding: 10px; margin-bottom: 15px; font-size: 14px; }
.modal-footer { display: flex; justify-content: space-between; gap: 15px; margin-top: 10px; }
.modal-footer .btn { flex: 1; }
</style>