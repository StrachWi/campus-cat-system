<template>
  <view class="auth-container">
    <view class="tabs">
      <text :class="{'active': isLogin}" @click="switchTab(true)">登录</text>
      <text :class="{'active': !isLogin}" @click="switchTab(false)">注册</text>
    </view>
    
    <view class="form-box">
      <input v-model="form.username" placeholder="请输入用户名" class="input-field" />
      
      <view class="password-wrapper">
        <input v-model="form.password" :password="!showPassword" placeholder="请输入密码" class="input-field no-margin" />
        <text class="eye-icon" @click="showPassword = !showPassword">
          {{ showPassword ? '👁️' : '👁️‍🗨️' }}
        </text>
      </view>
      
      <button @click="handleSubmit" class="submit-btn">{{ isLogin ? '登录' : '立即注册' }}</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';

const isLogin = ref(true);
const form = ref({ username: '', password: '' });
const showPassword = ref(false);

const switchTab = (mode) => {
  isLogin.value = mode;
  form.value.username = '';
  form.value.password = '';
  showPassword.value = false;
};

const handleSubmit = () => {
  if (!form.value.username || !form.value.password) {
    uni.showToast({ title: '信息不完整', icon: 'none' });
    return;
  }
  
  const endpoint = isLogin.value ? '/api/login' : '/api/register';
  
  uni.request({
    url: `http://192.168.43.202:5000${endpoint}`,
    method: 'POST',
    data: form.value,
    success: (res) => {
      if (res.data.status === 'success') {
        uni.showToast({ title: '操作成功', icon: 'success' });
        
        if (!isLogin.value) {
          switchTab(true);
        } else {
          uni.setStorageSync('real_user_id', res.data.user_id);
          uni.setStorageSync('real_username', form.value.username);
          setTimeout(() => {
            uni.reLaunch({ url: '/pages/index/index' });
          }, 1500);
        }
      } else {
        uni.showToast({ title: res.data.message || '操作失败', icon: 'none' });
      }
    },
    fail: () => {
      uni.showToast({ title: '网络连接失败', icon: 'none' });
    }
  });
};
</script>

<style scoped>
.auth-container {
  padding: 40px 25px;
  background-color: #ffffff;
  min-height: 100vh;
}
.tabs {
  display: flex;
  justify-content: space-around;
  margin-bottom: 45px;
  font-size: 22px;
  font-weight: bold;
  color: #999;
}
.active {
  color: #ff8c00;
  border-bottom: 4px solid #ff8c00;
  padding-bottom: 8px;
}
.input-field {
  border: 1px solid #eeeeee;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 25px;
  font-size: 16px;
  background-color: #fafafa;
}
.password-wrapper {
  position: relative;
  margin-bottom: 25px;
}
.no-margin {
  margin-bottom: 0;
  padding-right: 50px;
}
.eye-icon {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  padding: 5px;
}
.submit-btn {
  background-color: #ff8c00;
  color: white;
  border-radius: 25px;
  margin-top: 15px;
  height: 50px;
  line-height: 50px;
  font-size: 18px;
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
}
</style>