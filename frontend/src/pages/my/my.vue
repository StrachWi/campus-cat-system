<template>
  <view class="my-container">
    <!-- 1. 用户信息卡片 -->
    <view class="user-header">
      <image class="avatar" :src="userAvatar" mode="aspectFill" @click="chooseAvatar"></image>
      <view class="user-info">
        <view class="nickname-row" @click="showNicknameModal = true">
          <text class="nickname">{{ userNickname }}</text>
          <text class="edit-icon">✎</text>
        </view>
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

      <view class="menu-item" @click="showAccountModal = true">
        <view class="menu-left">
          <text class="icon">🔐</text>
          <text>账号管理</text>
        </view>
        <text class="arrow">›</text>
      </view>

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

    <!-- 管理员密码弹窗 -->
    <view v-if="verify" class="modal-mask" @click="verify=false">
      <view @click.stop class="admin-pwd-box">
        <input v-model="passwd" type="safe-password" placeholder="请输入管理员密码" class="input1"/>
        <button @click="goToAdmin">确定</button>
      </view>
    </view>

    <!-- ========== 昵称修改弹窗 ========== -->
    <view v-if="showNicknameModal" class="modal-mask" @click="showNicknameModal = false">
      <view class="form-modal" @click.stop>
        <text class="modal-title">修改昵称</text>
        <input v-model="editNickname" class="input-field" placeholder="请输入新昵称" />
        <view class="modal-actions">
          <button class="btn-cancel" @click="showNicknameModal = false">取消</button>
          <button class="btn-confirm" @click="saveNickname">保存</button>
        </view>
      </view>
    </view>

    <!-- ========== 账号管理弹窗 ========== -->
    <view v-if="showAccountModal" class="modal-mask" @click="showAccountModal = false">
      <view class="form-modal" @click.stop>
        <text class="modal-title">账号管理</text>
        <view class="account-options">
          <view class="account-option" @click="openPasswordModal">
            <text class="option-icon">🔑</text>
            <text class="option-text">修改密码</text>
            <text class="option-arrow">›</text>
          </view>
          <view class="account-option" @click="handleLogout">
            <text class="option-icon">🚪</text>
            <text class="option-text">退出登录</text>
            <text class="option-arrow">›</text>
          </view>
          <view class="account-option danger-option" @click="openDeleteModal">
            <text class="option-icon">🗑️</text>
            <text class="option-text">注销账号</text>
            <text class="option-arrow">›</text>
          </view>
        </view>
        <button class="btn-cancel" @click="showAccountModal = false" style="margin-top:12px;width:100%;">关闭</button>
      </view>
    </view>

    <!-- ========== 修改密码弹窗 ========== -->
    <view v-if="showPasswordModal" class="modal-mask" @click="showPasswordModal = false">
      <view class="form-modal" @click.stop>
        <text class="modal-title">修改密码</text>
        <input v-model="pwdForm.old_password" type="safe-password" class="input-field" placeholder="请输入原密码" />
        <input v-model="pwdForm.new_password" type="safe-password" class="input-field" placeholder="请输入新密码（至少6位）" />
        <input v-model="pwdForm.confirm_password" type="safe-password" class="input-field" placeholder="请再次输入新密码" />
        <view class="modal-actions">
          <button class="btn-cancel" @click="showPasswordModal = false">取消</button>
          <button class="btn-confirm" @click="submitChangePassword">确认修改</button>
        </view>
      </view>
    </view>

    <!-- ========== 注销账号确认弹窗 ========== -->
    <view v-if="showDeleteModal" class="modal-mask" @click="showDeleteModal = false">
      <view class="form-modal" @click.stop>
        <text class="modal-title" style="color:#e03131;">⚠️ 注销账号</text>
        <text class="delete-warning">注销后所有数据将被清除，此操作不可撤销！</text>
        <input v-model="deletePassword" type="safe-password" class="input-field" placeholder="请输入密码以确认注销" />
        <view class="modal-actions">
          <button class="btn-cancel" @click="showDeleteModal = false">取消</button>
          <button class="btn-danger" @click="submitDeleteAccount">确认注销</button>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { config } from '@/config.js';
import { onShow } from '@dcloudio/uni-app';

const DEFAULT_AVATAR = 'https://images.unsplash.com/photo-1533738363-b7f9aef128ce?w=200&h=200&fit=crop';

const myUserId = ref('');
const user_ID = ref(0);
const isExpanded = ref(false);
const catissued = ref([]);
const verify = ref(false);
const passwd = ref('');

// ---- 用户个人资料 ----
const userAvatar = ref(DEFAULT_AVATAR);
const userNickname = ref('热心校园铲屎官');

// ---- 昵称修改弹窗 ----
const showNicknameModal = ref(false);
const editNickname = ref('');

// ---- 账号管理弹窗 ----
const showAccountModal = ref(false);
const showPasswordModal = ref(false);
const showDeleteModal = ref(false);
const deletePassword = ref('');

const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
});

// ==================== 工具函数 ====================

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

const resolveAvatarUrl = (url) => {
  if (!url) return DEFAULT_AVATAR;
  return formatImageUrl(url);
};

// ==================== 加载用户资料 ====================

const fetchUserProfile = () => {
  if (!user_ID.value) return;
  uni.request({
    url: `${config.baseUrl}/api/user/profile?user_id=${user_ID.value}`,
    method: 'GET',
    success: (res) => {
      if (res.data?.status === 'success') {
        const profile = res.data.data;
        userNickname.value = profile.nickname || profile.username || '热心校园铲屎官';
        userAvatar.value = resolveAvatarUrl(profile.avatar_url);
      }
    },
  });
};

// ==================== 头像上传（含裁剪） ====================

const chooseAvatar = () => {
  if (!user_ID.value) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    crop: {
      quality: 80,
      width: 200,
      height: 200,
      resize: true,
    },
    success: (res) => {
      const tempPath = res.tempFilePaths[0];
      uni.showLoading({ title: '上传中...' });
      uni.uploadFile({
        url: `${config.baseUrl}/api/user/avatar`,
        filePath: tempPath,
        name: 'image',
        formData: { user_id: String(user_ID.value) },
        success: (uploadRes) => {
          uni.hideLoading();
          const data = JSON.parse(uploadRes.data || '{}');
          if (data.status === 'success') {
            uni.showToast({ title: '头像更新成功', icon: 'success' });
            userAvatar.value = resolveAvatarUrl(data.avatar_url);
          } else {
            uni.showToast({ title: data.message || '上传失败', icon: 'none' });
          }
        },
        fail: () => {
          uni.hideLoading();
          uni.showToast({ title: '上传失败，请检查网络', icon: 'none' });
        },
      });
    },
  });
};

// ==================== 昵称修改 ====================

const saveNickname = () => {
  const name = editNickname.value.trim();
  if (!name) {
    uni.showToast({ title: '昵称不能为空', icon: 'none' });
    return;
  }
  uni.request({
    url: `${config.baseUrl}/api/user/profile`,
    method: 'PUT',
    data: { user_id: user_ID.value, nickname: name },
    success: (res) => {
      if (res.data?.status === 'success') {
        userNickname.value = name;
        showNicknameModal.value = false;
        uni.showToast({ title: '昵称已更新', icon: 'success' });
      } else {
        uni.showToast({ title: res.data?.message || '修改失败', icon: 'none' });
      }
    },
    fail: () => {
      uni.showToast({ title: '网络连接失败', icon: 'none' });
    },
  });
};

// ==================== 账号管理 ====================

const openPasswordModal = () => {
  showAccountModal.value = false;
  pwdForm.old_password = '';
  pwdForm.new_password = '';
  pwdForm.confirm_password = '';
  showPasswordModal.value = true;
};

const submitChangePassword = () => {
  const { old_password, new_password, confirm_password } = pwdForm;
  if (!old_password || !new_password || !confirm_password) {
    uni.showToast({ title: '请填写所有密码字段', icon: 'none' });
    return;
  }
  if (new_password.length < 6) {
    uni.showToast({ title: '新密码至少6位', icon: 'none' });
    return;
  }
  if (new_password !== confirm_password) {
    uni.showToast({ title: '两次输入的新密码不一致', icon: 'none' });
    return;
  }
  uni.request({
    url: `${config.baseUrl}/api/user/password`,
    method: 'PUT',
    data: { user_id: user_ID.value, old_password, new_password },
    success: (res) => {
      if (res.data?.status === 'success') {
        uni.showToast({ title: '密码修改成功', icon: 'success' });
        showPasswordModal.value = false;
      } else {
        uni.showToast({ title: res.data?.message || '修改失败', icon: 'none' });
      }
    },
    fail: () => {
      uni.showToast({ title: '网络连接失败', icon: 'none' });
    },
  });
};

const handleLogout = () => {
  uni.showModal({
    title: '退出登录',
    content: '确定要退出当前账号吗？',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('real_user_id');
        uni.removeStorageSync('real_username');
        uni.removeStorageSync('admin_token');
        showAccountModal.value = false;
        uni.reLaunch({ url: '/pages/login/login' });
      }
    },
  });
};

const openDeleteModal = () => {
  showAccountModal.value = false;
  deletePassword.value = '';
  showDeleteModal.value = true;
};

const submitDeleteAccount = () => {
  if (!deletePassword.value) {
    uni.showToast({ title: '请输入密码', icon: 'none' });
    return;
  }
  uni.showModal({
    title: '最终确认',
    content: '注销后账号及关联数据将被永久清除，确定继续？',
    success: (modalRes) => {
      if (!modalRes.confirm) return;
      uni.request({
        url: `${config.baseUrl}/api/user/account`,
        method: 'DELETE',
        data: { user_id: user_ID.value, password: deletePassword.value },
        success: (res) => {
          if (res.data?.status === 'success') {
            uni.removeStorageSync('real_user_id');
            uni.removeStorageSync('real_username');
            uni.removeStorageSync('admin_token');
            uni.showToast({ title: '账号已注销', icon: 'success' });
            setTimeout(() => {
              uni.reLaunch({ url: '/pages/login/login' });
            }, 1500);
          } else {
            uni.showToast({ title: res.data?.message || '注销失败', icon: 'none' });
          }
        },
        fail: () => {
          uni.showToast({ title: '网络连接失败', icon: 'none' });
        },
      });
    },
  });
};

// ==================== 原有功能 ====================

const getIssued = () => {
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
    },
  });
};

onShow(() => {
  myUserId.value = uni.getStorageSync('mock_user_id');
  user_ID.value = uni.getStorageSync('real_user_id');
  getIssued();
  fetchUserProfile();
});

const showFeatureToast = () => {
  uni.showToast({
    title: '功能努力开发中~',
    icon: 'none',
  });
};

const goToAdmin = () => {
  if (!passwd.value) {
    uni.showToast({ title: '请输入管理员密码', icon: 'none' });
    return;
  }
  verify.value = false;

  uni.request({
    url: `${config.baseUrl}/api/admin/login`,
    method: 'POST',
    data: { password: passwd.value },
    success: (res) => {
      if (res.data.status === 'success') {
        uni.setStorageSync('admin_token', res.data.admin_token);
        uni.navigateTo({ url: '/pages/admin/admin' });
        uni.showToast({
          title: '即将前往审核端',
          icon: 'success',
        });
      } else {
        uni.showToast({
          title: '密码错误',
          icon: 'none',
        });
        verify.value = true;
      }
    },
    fail: () => {
      uni.showToast({ title: '后端未启动或地址不通', icon: 'none' });
      verify.value = true;
    },
  });
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
.nickname-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 5px;
}
.nickname {
  font-size: 20px;
  font-weight: bold;
  color: #ffffff;
}
.edit-icon {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
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
  max-height: 500px;
  transition: max-height 0.2s ease-in;
}
.content-inner { padding: 10px; }
.cat-card { background-color: #fff; border-radius: 16px; padding: 16px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); }
.card-header { display: flex; align-items: center; margin-bottom: 16px; }
.cat-avatar { width: 60px; height: 60px; border-radius: 50%; margin-right: 12px; background-color: #eee; }
.cat-info { flex: 1; }
.name-row { display: flex; align-items: center; margin-bottom: 6px; }
.name { font-size: 18px; font-weight: bold; color: #333; margin-right: 8px; }

/* 管理员弹窗 */
.admin-pwd-box {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  min-width: 280px;
}
.input1 {
  background-color: #d3d3d3;
  border-style: inset;
  margin: 15px;
  padding: 8px 12px;
  border-radius: 6px;
}

/* ===== 通用弹窗 ===== */
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0,0,0,0.5);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-modal {
  background: #fff;
  border-radius: 16px;
  padding: 24px 20px;
  width: 84%;
  max-width: 360px;
}

.modal-title {
  display: block;
  text-align: center;
  font-size: 18px;
  font-weight: 700;
  color: #222;
  margin-bottom: 18px;
}

.input-field {
  box-sizing: border-box;
  width: 100%;
  height: 44px;
  background: #f5f7fa;
  border-radius: 10px;
  padding: 0 14px;
  font-size: 14px;
  margin-bottom: 14px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 6px;
}

.btn-cancel {
  flex: 1;
  height: 42px;
  line-height: 42px;
  border-radius: 10px;
  font-size: 15px;
  background: #f1f3f5;
  color: #666;
}

.btn-confirm {
  flex: 1;
  height: 42px;
  line-height: 42px;
  border-radius: 10px;
  font-size: 15px;
  background: #ff8c00;
  color: #fff;
}

.btn-danger {
  flex: 1;
  height: 42px;
  line-height: 42px;
  border-radius: 10px;
  font-size: 15px;
  background: #e03131;
  color: #fff;
}

/* 账号管理选项 */
.account-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.account-option {
  display: flex;
  align-items: center;
  padding: 16px 12px;
  border-radius: 10px;
  background: #f8f9fa;
  gap: 12px;
}

.danger-option {
  background: #fff5f5;
}

.option-icon {
  font-size: 20px;
}

.option-text {
  flex: 1;
  font-size: 15px;
  color: #333;
  font-weight: 500;
}

.danger-option .option-text {
  color: #e03131;
}

.option-arrow {
  color: #ccc;
  font-size: 18px;
}

.delete-warning {
  display: block;
  text-align: center;
  font-size: 13px;
  color: #e03131;
  margin-bottom: 16px;
  line-height: 1.6;
}
</style>
