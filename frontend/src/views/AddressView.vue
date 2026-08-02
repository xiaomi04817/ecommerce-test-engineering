<template>
  <div class="address-container">
    <el-container>
      <el-header class="page-header">
        <div class="header-left">
          <el-button text @click="$router.push('/products')">
            <el-icon><ArrowLeft /></el-icon>
            返回商品列表
          </el-button>
          <h2>收货地址</h2>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="openAddDialog">添加新地址</el-button>
        </div>
      </el-header>

      <el-main>
        <!-- Loading -->
        <div v-if="loading" class="loading-area">
          <el-skeleton :rows="3" animated />
        </div>

        <!-- Empty -->
        <el-empty v-else-if="addresses.length === 0" description="暂无收货地址">
          <el-button type="primary" @click="openAddDialog">添加地址</el-button>
        </el-empty>

        <!-- Address List -->
        <div v-else class="address-list">
          <el-card
            v-for="addr in addresses"
            :key="addr.id"
            class="address-card"
            :class="{ 'is-default': addr.isDefault }"
          >
            <div class="address-content">
              <div class="address-header">
                <span class="receiver">{{ addr.receiverName }}</span>
                <span class="phone">{{ addr.phone }}</span>
                <el-tag v-if="addr.isDefault" type="success" size="small">默认</el-tag>
              </div>
              <div class="address-detail">
                {{ addr.province }}{{ addr.city }}{{ addr.district }} {{ addr.detail }}
              </div>
            </div>
            <div class="address-actions">
              <el-button size="small" @click="openEditDialog(addr)">编辑</el-button>
              <el-button
                size="small"
                type="danger"
                @click="handleDelete(addr)"
              >
                删除
              </el-button>
            </div>
          </el-card>
        </div>
      </el-main>
    </el-container>

    <!-- Add/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑地址' : '添加新地址'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="收件人" prop="receiverName">
          <el-input v-model="form.receiverName" placeholder="请输入收件人姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="省份" prop="province">
          <el-input v-model="form.province" placeholder="请输入省份" />
        </el-form-item>
        <el-form-item label="城市" prop="city">
          <el-input v-model="form.city" placeholder="请输入城市" />
        </el-form-item>
        <el-form-item label="区/县" prop="district">
          <el-input v-model="form.district" placeholder="请输入区/县" />
        </el-form-item>
        <el-form-item label="详细地址" prop="detail">
          <el-input
            v-model="form.detail"
            type="textarea"
            :rows="2"
            placeholder="请输入详细地址（5-100字）"
          />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="form.isDefault" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import api from '../utils/api'

const addresses = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  receiverName: '',
  phone: '',
  province: '',
  city: '',
  district: '',
  detail: '',
  isDefault: false
})

const rules: FormRules = {
  receiverName: [
    { required: true, message: '请输入收件人姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '收件人姓名长度为2-20位', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' }
  ],
  province: [
    { required: true, message: '请输入省份', trigger: 'blur' }
  ],
  city: [
    { required: true, message: '请输入城市', trigger: 'blur' }
  ],
  district: [
    { required: true, message: '请输入区/县', trigger: 'blur' }
  ],
  detail: [
    { required: true, message: '请输入详细地址', trigger: 'blur' },
    { min: 5, max: 100, message: '详细地址长度为5-100字', trigger: 'blur' }
  ]
}

async function fetchAddresses() {
  loading.value = true
  try {
    const res = await api.get('/addresses')
    addresses.value = res.data.data || []
  } catch {
    addresses.value = []
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.receiverName = ''
  form.phone = ''
  form.province = ''
  form.city = ''
  form.district = ''
  form.detail = ''
  form.isDefault = false
  editingId.value = null
  formRef.value?.resetFields()
}

function openAddDialog() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(addr: any) {
  isEdit.value = true
  editingId.value = addr.id
  form.receiverName = addr.receiverName
  form.phone = addr.phone
  form.province = addr.province
  form.city = addr.city
  form.district = addr.district
  form.detail = addr.detail
  form.isDefault = addr.isDefault || false
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    if (isEdit.value && editingId.value) {
      await api.put(`/addresses/${editingId.value}`, {
        receiverName: form.receiverName,
        phone: form.phone,
        province: form.province,
        city: form.city,
        district: form.district,
        detail: form.detail,
        isDefault: form.isDefault
      })
      ElMessage.success('地址已更新')
    } else {
      await api.post('/addresses', {
        receiverName: form.receiverName,
        phone: form.phone,
        province: form.province,
        city: form.city,
        district: form.district,
        detail: form.detail,
        isDefault: form.isDefault
      })
      ElMessage.success('地址已添加')
    }
    dialogVisible.value = false
    fetchAddresses()
  } catch {
    // Error handled by interceptor
  } finally {
    submitting.value = false
  }
}

async function handleDelete(addr: any) {
  try {
    await ElMessageBox.confirm(
      `确定要删除地址"${addr.receiverName} ${addr.phone}"吗？`,
      '确认删除',
      { type: 'warning' }
    )
  } catch {
    return
  }
  try {
    await api.delete(`/addresses/${addr.id}`)
    ElMessage.success('地址已删除')
    fetchAddresses()
  } catch {
    // Error handled by interceptor
  }
}

onMounted(() => {
  fetchAddresses()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
}

.loading-area {
  padding: 40px 0;
}

.address-list {
  max-width: 700px;
}

.address-card {
  margin-bottom: 12px;
}

.address-card.is-default {
  border-color: #67c23a;
}

.address-content {
  margin-bottom: 12px;
}

.address-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.receiver {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.phone {
  color: #909399;
  font-size: 14px;
}

.address-detail {
  color: #606266;
  font-size: 14px;
}

.address-actions {
  display: flex;
  gap: 8px;
}
</style>
