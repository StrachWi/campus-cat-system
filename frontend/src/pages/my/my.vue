<template>
  <view class="my-container">
    <!-- 1. 用户信息卡片 (目前使用模拟的默认信息) -->
    <view class="user-header">
      <image class="avatar" src="https://images.unsplash.com/photo-1533738363-b7f9aef128ce?w=200&h=200&fit=crop" mode="aspectFill"></image>
      <view class="user-info">
        <text class="nickname">热心校园铲屎官</text>
        <text class="user-id">身份标识码：{{ user_ID || '暂无' }}</text>
      </view>
    </view>

    <!-- 2. 数据概览 (装饰性数据，后续可连后端) -->
    <view class="stats-card">
      <view class="stat-item">
        <text class="num">3</text>
        <text class="label">我的认领</text>
      </view>
      <view class="stat-item">
        <text class="num">1</text>
        <text class="label">我的发现</text>
      </view>
      <view class="stat-item">
        <text class="num">Lv.2</text>
        <text class="label">爱心等级</text>
      </view>
    </view>

    <!-- 3. 普通用户功能列表 -->
    <view class="menu-list">
      <view class="menu-item" @click="showFeatureToast">
        <view class="menu-left">
          <text class="icon">🍱</text>
          <text>我认领的喂养时段</text>
        </view>
        <text class="arrow">›</text>
      </view>
      
      <view class="menu-item" @click="isExpanded = !isExpanded">
        <view class="menu-left">
          <text class="icon">📸</text>
          <text>我提报的猫咪档案</text>
        </view>
		<text class="fold-tip">点击展开/收起</text>
		<text :class="['fold-icon', isExpanded ? 'icon-rotated' : '']">▶</text>
      </view>
	  <div class="collapse-content" :class="{ 'is-expanded': isExpanded }">
	    <div class="content-inner">
	          <view class="cat-list">
	            <view class="cat-card" v-for="cat in catissued" :key="cat.catname">
	              <view class="card-header" >
	                <image class="cat-avatar" :src="formatImageUrl(cat.avatar_url)" mode="aspectFill"></image>
	                <view class="cat-info">
	                  <view class="name-row">
	                    <text class="name">{{ cat.catname }}</text>
	                  </view>
	                  <text class="location">📍 {{ cat.location }}</text>
	                </view>
					<text>  描述{{cat.desc}}</text>
	              </view>
	            </view>
	          </view>
	    </div>
	  </div>

      <view class="menu-item" @click="showFeatureToast">
        <view class="menu-left">
          <text class="icon">⚙️</text>
          <text>系统设置</text>
        </view>
        <text class="arrow">›</text>
      </view>
    </view>

    <!-- 4. 教师/管理员审核入口 (核心功能区) -->
    <view class="admin-section" @click="verify=true">
      <view class="admin-card">
        <view class="admin-left">
          <text class="admin-icon">🛡️</text>
          <view class="admin-text">
            <text class="admin-title">管理员审核端</text>
            <text class="admin-subtitle">查看并审核全校新提交的猫咪</text>
          </view>
        </view>
        <text class="arrow admin-arrow">›</text>
      </view>
    </view>
	
	<view v-if="verify" class="modal-mask" @click="verify=false">
		<view @click.stop>
			<input v-model="passwd" type="safe-password" placeholder="请输入管理员密码" class="input1"/>
			<button @click="goToAdmin">确定</button>
		</view>
	</view>

  </view>
</template>

<script setup>
import { ref } from 'vue';
import {config} from '@/config.js';
import { onShow } from '@dcloudio/uni-app';

const myUserId = ref('');
const user_ID = ref(0);
const isExpanded = ref(false);
const catissued = ref([]);
const verify = ref(false);
const passwd = ref('');

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
const getIssued = ()=>{
	uni.request({
	  url: `${config.baseUrl}/api/user/issued?user_id=${user_ID.value}`,
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
	      catissued.value = data;
	    }
	  }
	});
};

// 每次切到“我的”页面，都去本地缓存里取一下我们之前生成的虚拟身份ID
onShow(() => {
  myUserId.value = uni.getStorageSync('mock_user_id');
  user_ID.value = uni.getStorageSync('real_user_id');
  getIssued();
});

const showFeatureToast = () => {
  uni.showToast({
    title: '功能努力开发中~',
    icon: 'none'
  });
};

const goToAdmin = () => {
  if (!passwd.value) {
    uni.showToast({ title: '请输入管理员密码', icon: 'none' });
    return;
  }
  verify.value=false;
  
  uni.request({
	  url:`${config.baseUrl}/api/admin/login`,method:'POST',
	  data:{password:passwd.value},
	  success: (res) => {
	  	if(res.data.status === 'success'){
			uni.setStorageSync('admin_token',res.data.admin_token);
			uni.navigateTo({ url: '/pages/admin/admin' });
			uni.showToast({
			  title: '即将前往审核端',
			  icon: 'success'
			});
		}else {
			uni.showToast({
			  title: '密码错误',
        icon: 'none'
			});
			verify.value = true;
		}
	  },
    fail: () => {
      uni.showToast({ title: '后端未启动或地址不通', icon: 'none' });
      verify.value = true;
    }
  })
  passwd.value = '';
};
</script>

<style scoped>
.my-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding-bottom: 30px;
}

/* 用户头部信息 */
.user-header {
  background: linear-gradient(135deg, #ffb74d, #ff8c00);
  padding: 60px 20px 40px;
  display: flex;
  align-items: center;
  border-radius: 0 0 30px 30px;
}
.avatar {
  width: 70px;
  height: 70px;
  border-radius: 35px;
  border: 3px solid rgba(255, 255, 255, 0.4);
  margin-right: 15px;
  background-color: #eee;
}
.user-info {
  display: flex;
  flex-direction: column;
}
.nickname {
  font-size: 20px;
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 5px;
}
.user-id {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  background-color: rgba(0, 0, 0, 0.1);
  padding: 3px 8px;
  border-radius: 12px;
  display: inline-block;
}

/* 数据概览卡片 */
.stats-card {
  background-color: #ffffff;
  margin: -20px 15px 15px;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  justify-content: space-around;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  position: relative;
  z-index: 10;
}
.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.num {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}
.label {
  font-size: 12px;
  color: #666;
}

/* 列表菜单 */
.menu-list {
  background-color: #ffffff;
  margin: 0 15px 20px;
  border-radius: 16px;
  padding: 5px 15px;
}
.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 5px;
  border-bottom: 1px solid #f5f5f5;
}
.menu-item:last-child {
  border-bottom: none;
}
.menu-left {
  display: flex;
  align-items: center;
  font-size: 15px;
  color: #333;
}
.icon {
  margin-right: 12px;
  font-size: 18px;
}
.arrow {
  color: #ccc;
  font-weight: bold;
}
.fold-tip { color: #666; font-size: 13px; }
.fold-icon { color: #333; margin-left: 8px; transition: transform 0.3s; }

/* 教师/管理员入口 */
.admin-section {
  margin: 0 15px;
}
.admin-card {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border-radius: 16px;
  padding: 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0, 242, 254, 0.2);
}
.admin-left {
  display: flex;
  align-items: center;
}
.admin-icon {
  font-size: 28px;
  margin-right: 12px;
}
.admin-text {
  display: flex;
  flex-direction: column;
}
.admin-title {
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 4px;
}
.admin-subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 11px;
}
.admin-arrow {
  color: rgba(255, 255, 255, 0.8);
}

.collapse-header {
  cursor: pointer;
  padding: 10px;
  background: #f5f5f5;
  display: flex;
  justify-content: space-between;
}
.icon-rotated { transform: rotate(90deg); transition: transform 0.3s; }

/* 折叠动画核心 */
.collapse-content {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease-out;
}
.is-expanded {
  max-height: 500px; /* 设置一个足够大的值 */
  transition: max-height 0.2s ease-in;
}
.content-inner { padding: 10px; }
.cat-card { background-color: #fff; border-radius: 16px; padding: 16px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); }
.card-header { display: flex; align-items: center; margin-bottom: 16px; }
.cat-avatar { width: 60px; height: 60px; border-radius: 50%; margin-right: 12px; background-color: #eee; }
.cat-info { flex: 1; }
.name-row { display: flex; align-items: center; margin-bottom: 6px; }
.name { font-size: 18px; font-weight: bold; color: #333; margin-right: 8px; }
.input1{background-color: #d3d3d3;border-style: inset; margin: 15px;}
.modal-mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); z-index: 999; display: flex; align-items: center; justify-content: center;}
</style>
