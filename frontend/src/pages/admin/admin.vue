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
	  <view :class="['tab-item', currentTab === 'goods' ? 'active-tab' : '']" @click="currentTab = 'goods'">物资管理</view>
	  <view :class="['tab-item', currentTab === 'bank' ? 'active-tab' : '']" @click="currentTab = 'bank'">账目管理</view>
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
	
	<!-- 物资管理界面-->
	<view v-show="currentTab ==='goods'">
		<view class="culumn">
			<view>
				<view>
					<text>物品存余</text>
				</view>
			</view>
		</view>
		
		<view class="culumn">
			<view>
				<view><text>上传物品改动</text></view>
				<view v-for="goods in goodsList" :key="goods.item" class="cat-list1">
					<view>
						<text class="iname">{{goods.item}}:</text>
						<text class="inum">{{goods.op===0 ? goods.num+goods.temp :goods.num-goods.temp}}</text>
						<view class="changehead">
							<button :disabled="goods.op===1" @click="goods.op=1" class="but1">存</button>
							<button :disabled="goods.op===0" @click="goods.op=0" class="but1">取</button>
						</view>
						<text class="iname">数量：</text>
						<view class="changehead">
							<button :disabled="goods.temp <=0" @click="goods.temp--" class="but2">-</button>
							<input type="text" v-model.number="goods.temp" @blur="handBlur(goods)" class="input1"/>
							<button :disabled="goods.op===1&&goods.temp>=goods.num" @click="goods.temp++" class="but2">+</button>
						</view>
						<text class="iname">备注：</text>
						<input type="text" v-model="goods.remark" placeholder="填入备注" class="input2"/>
						<text></text>
					</view>
				</view>
			</view>
		</view>
		
		<view class="mask" v-show="showGoodsform" @click="showGoodsform=false">
			<view class="confirm">
				<text class="head2">您已做如下改动</text>
				<view v-for="goods in goodsList" :key="goods.item" class="region">
					<view v-if="goods.temp!=0">
						<text class="nape">{{goods.op===0 ? '存' : '取'}}{{goods.temp}}个{{goods.item}}</text><br>
					</view>
				</view>
				<button @click="handleGoods">确认</button>
			</view>
		</view>
		
		<view>
			<view class="Chbut">
				<button @click="showGoodsform=true">改动</button>
			</view>
		</view>
	</view>
	<!-- 账目管理界面-->
	<view v-show="currentTab ==='bank' ">
		<view class="center">
			<view>
				<!-- 总金额-->
				<text class="head2">当前金额</text>
			</view>
			<view>
				<!-- 操作历史-->
				<view v-for="op in bankList" :key="op.time">
					<text class="nape">{{op.name}}于{{op.time}}{{op.type}}{{op.num}}</text>
				</view>
			</view>
			<view class="bill" v-show="Banksta!=0" @click.stop>
				<!--上报表-->
				<text>金额：</text>
				<input type="text" v-model.number="billnum" placeholder="输入金额" class="input1" />
				<text>备注：</text>
				<input type="text" v-model="billmark" placeholder="备注" class="input2"/>
				<view  @click="chooseImage" class="upload-section">
				  <image v-if="tempImagePath" :src="tempImagePath" mode="aspectFill" class="preview-img"></image>
				  <view v-else class="upload-placeholder">
				    <text class="plus-icon">+</text>
				    <text>上传支票</text>
				  </view>
				</view>
				<button @click="handleBank" class="but3">{{Banksta===1? '存':'取'}}</button>
				<button @click="Banksta=0">取消</button>
			</view>
			<view  @click.stop v-if="Banksta===0">
				<button @click="Banksta=1" class="but4"> 存</button>
				<button @click="Banksta=2" class="but4">取</button>
				<!--选择按钮-->
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
import { computed, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { config } from '@/config.js';

const currentTab = ref('pending'); // 当前激活的Tab，默认待审核
const user_id = ref('');
const pendingCats = ref([]);
const publishedCats = ref([]);
const goodsList = ref([{item:'猫粮',num:3,temp:0,op:0 ,remark:''}]);
const bankList = ref([]);

// 弹窗相关变量
const showEditModal = ref(false);
const editForm = ref({ id: '', name: '', location: '', character_desc: '' });

const tempImagePath = ref('');
const billnum=ref(0);
const billmark=ref('');
const Banksta = ref(0);
const showGoodsform = ref(false);
const handBlur = (goods) =>{
	if (typeof goods.temp !== 'number' || isNaN(goods.temp) || goods.temp < 0) {
	        goods.temp = 0;
	} else {
		goods.temp = Math.floor(goods.temp);
	}
};
const chooseImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      tempImagePath.value = res.tempFilePaths[0];
    }
  });
};

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


const handleGoods = () =>{
	const templist = goodsList.value.filter(ch =>{
		return ch.temp != 0;
	});
	for (const goods in goodsList){
		uni.request({
			url: `${config.baseUrl}/api/admin/goods`,method:'POST',data:{user_id: user_id , operate:goods.op+1 , num:goods.temp , item: goods.item , remark: goods.remark}
		});
	};
};

const handleBank = ()=>{
	if(billnum.value===0){
		uni.showToast({ title: '没有做出改动', icon: 'none' });
		return;
	}
	
	if (!tempImagePath.value) {
	  uni.showToast({ title: '请至少上传一张照片', icon: 'none' });
	  return;
	}
	
	uni.uploadFile({
	  url: `${config.baseUrl}/api/admin/bank`,
	  method: 'POST',
	  filePath: tempImagePath.value,
	  name: 'image',
	  formData: {
	    user_id:user_id,
		num: billnum,
		type: Banksta,
		remark: billmark
	  },
	  success: (res) => {
	    uni.hideLoading();
	    let data = JSON.parse(res.data);
	    
	    if (data.status === 'success') {
	      uni.showToast({ title: '带图提报成功！', icon: 'success' });
	    } else {
	      uni.showToast({ title: '提交失败，请重试', icon: 'none' });
	    }
	  },
	  fail: (err) => {
	    uni.hideLoading();
	    console.error(err);
	    uni.showToast({ title: '上传失败，请检查网络', icon: 'none' });
	  }
	});
	Banksta = 0;
};


const fetchGoodslist = ()=>{
	const temp =ref([]);
	uni.request({
	  url: `${config.baseUrl}/api/admin/pending_cats`, //暂定
	  success: (res) => { if (res.data?.status === 'success') temp.value = res.data.data; }
	});
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
onShow(() => { user_id.value = uni.getStorageSync('mock_user_id'); fetchPendingCats(); fetchPublishedCats(); });
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

/*物资样式*/
.cat-list1{background-color: #55aaff; margin: 8px; border-radius: 10px; padding: 10px;}
.iname{color: #005500; margin: 10px;}
.inum{color: #aa0000; margin: 10px;}
.but1{width: 7%;font-size: 10px;margin: 5px; background-color: #f56c6c; display: flex;justify-content: center;}
.but2{width: 5%;margin: 2px; padding: 0px; display: flex;justify-content: center;background-color: #ffaa00;}
.but3{width: 50%; padding: 0px; display: flex;justify-content: center;background-color: #ffaa00; margin-bottom: 4px;}
.but4{background-color: #4facfe;}
.input1{background-color: #d3d3d3;width: 15%;border-style: inset;}
.input2{background-color: #d3d3d3;width: 60%;border-style: inset;margin: 10px;}
.changehead{display: flex; align-items: center;}
.culumn{margin: 5px;padding: 5px;background-color: #aaaaff;border-radius: 10px;}
.Chbut{position: fixed; bottom: 0%; width: 100%;display:flex; justify-content: center;padding: 5px; background-color: #ff5500;}
.mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); z-index: 999; display: flex;justify-content: center;  align-items: center; }
.confirm{position: fixed; padding: 5px; background-color: #d3d3d3;width: 50%;}
.nape{padding: 2px;margin: 4px;}
.region{background-color: #d3d3d3;padding: 3px;}
.head2{margin: 2px;color: #005500;}
.center{justify-content: space-evenly;   align-items: center;}
.bill{background-color: #aaaaff; border-radius: 10px; padding: 5px;}
.plus-icon { font-size: 32px; color: #ccc; margin-bottom: 4px; }
.preview-img { width: 120px; height: 120px; border-radius: 12px; }
.upload-section { display: flex; justify-content: center; margin-bottom: 25px;}
.upload-placeholder {width: 100%;height: 120px; background-color: #f5f5f5; border: 2px dashed #e0e0e0; border-radius: 12px; display: flex; flex-direction: column; justify-content: center; align-items: center; color: #999; font-size: 12px;margin: 6rpx; }
</style>