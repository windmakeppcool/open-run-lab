<!--
  用户与权限：纯静态规划页（对应后台管理规划 Step 4 RBAC）
  不发任何请求、不放真实数据，仅展示设计稿。
-->
<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">TEAM & ACCESS</div>
        <h1>用户与权限</h1>
        <p>管理工作空间成员与项目访问范围。</p>
      </div>
    </div>

    <div class="compare-banner">
      权限模块规划中：以下为 RBAC 角色与授权范围的设计稿示意，不代表实际鉴权或账户数据，相关能力将在后台管理规划 Step 4 落地。
    </div>

    <div class="panel">
      <div class="table-head">
        <div>
          <h2 class="panel-title">工作空间成员</h2>
          <p class="panel-sub">管理员可管理用户，成员仅访问获授权的项目</p>
        </div>
      </div>
      <div class="table-wrap">
        <table class="people-table">
          <thead>
            <tr>
              <th>成员</th>
              <th>角色</th>
              <th>项目访问范围</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <div class="user-cell">
                  <div class="user-avatar">YL</div>
                  <div>
                    <strong>研究管理员</strong>
                    <span class="run-id">admin@example.local</span>
                  </div>
                </div>
              </td>
              <td>管理员</td>
              <td>全部项目</td>
              <td><span class="badge running">正常</span></td>
            </tr>
            <tr>
              <td>
                <div class="user-cell">
                  <div class="user-avatar">LX</div>
                  <div>
                    <strong>研究成员</strong>
                    <span class="run-id">member@example.local</span>
                  </div>
                </div>
              </td>
              <td>成员</td>
              <td>按项目授权（示例：qwen-lora-sft、resnet-classifier）</td>
              <td><span class="badge running">正常</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="table-foot">
        <span>以上为界面设计稿，非真实用户数据</span>
      </div>
    </div>
  </div>
</template>
