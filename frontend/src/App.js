import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Menu, Typography, Space } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  SettingOutlined,
  BarChartOutlined,
  ShieldOutlined,
  BellOutlined
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import EntityProfile from './components/EntityProfile';
import SecurityRules from './components/SecurityRules';
import RiskAssessment from './components/RiskAssessment';
import 'antd/dist/reset.css';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

function App() {
  const [collapsed, setCollapsed] = React.useState(false);
  const [selectedKey, setSelectedKey] = React.useState('dashboard');

  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      path: '/'
    },
    {
      key: 'risk-assessment',
      icon: <BarChartOutlined />,
      label: 'Risk Assessment',
      path: '/risk-assessment'
    },
    {
      key: 'entities',
      icon: <UserOutlined />,
      label: 'Entity Profiles',
      path: '/entities'
    },
    {
      key: 'security-rules',
      icon: <ShieldOutlined />,
      label: 'Security Rules',
      path: '/security-rules'
    },
    {
      key: 'alerts',
      icon: <BellOutlined />,
      label: 'Alerts & Patterns',
      path: '/alerts'
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      path: '/settings'
    }
  ];

  const handleMenuClick = ({ key }) => {
    setSelectedKey(key);
  };

  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider 
          collapsible 
          collapsed={collapsed} 
          onCollapse={setCollapsed}
          theme="dark"
          width={250}
        >
          <div style={{ 
            height: 64, 
            margin: 16, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: collapsed ? 'center' : 'flex-start'
          }}>
            <ShieldOutlined style={{ fontSize: 24, color: '#1890ff' }} />
            {!collapsed && (
              <Title level={4} style={{ 
                color: 'white', 
                margin: 0, 
                marginLeft: 12,
                fontSize: 16
              }}>
                RiskGuard
              </Title>
            )}
          </div>
          
          <Menu
            theme="dark"
            selectedKeys={[selectedKey]}
            mode="inline"
            onClick={handleMenuClick}
            items={menuItems.map(item => ({
              key: item.key,
              icon: item.icon,
              label: item.label
            }))}
          />
        </Sider>

        <Layout>
          <Header style={{ 
            padding: '0 24px', 
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0'
          }}>
            <Space>
              <Title level={3} style={{ margin: 0 }}>
                Cybersecurity Risk Scoring System
              </Title>
            </Space>
            
            <Space>
              <div style={{ 
                padding: '4px 12px', 
                background: '#f0f0f0', 
                borderRadius: 4,
                fontSize: 12,
                color: '#666'
              }}>
                v1.0.0
              </div>
            </Space>
          </Header>

          <Content style={{ 
            margin: 0, 
            minHeight: 280,
            background: '#f5f5f5'
          }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/risk-assessment" element={<RiskAssessment />} />
              <Route path="/entities" element={<EntityProfile />} />
              <Route path="/entities/:entityId" element={<EntityProfile />} />
              <Route path="/security-rules" element={<SecurityRules />} />
              <Route path="/alerts" element={<div style={{ padding: 24 }}>Alerts & Patterns - Coming Soon</div>} />
              <Route path="/settings" element={<div style={{ padding: 24 }}>Settings - Coming Soon</div>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;