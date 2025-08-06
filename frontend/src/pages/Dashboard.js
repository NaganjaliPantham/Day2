import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Button,
  Space,
  Badge,
  Progress,
  Spin,
  Alert,
  Divider,
  Typography,
  Tag
} from 'antd';
import {
  UserOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  RobotOutlined,
  ShieldOutlined
} from '@ant-design/icons';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { apiService, riskUtils, errorHandler, dataFormatter, chartConfig } from '../services/api';

const { Title, Text } = Typography;

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [entities, setEntities] = useState([]);
  const [modelInfo, setModelInfo] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [statsResponse, entitiesResponse, modelResponse] = await Promise.all([
        apiService.getDashboardStats(),
        apiService.getEntities(),
        apiService.getModelInfo()
      ]);

      if (statsResponse.status === 'success') {
        setDashboardStats(statsResponse.stats);
      }

      if (entitiesResponse.status === 'success') {
        setEntities(entitiesResponse.entities);
      }

      if (modelResponse.status === 'success') {
        setModelInfo(modelResponse.model_info);
      }
    } catch (error) {
      errorHandler.handleApiError(error, 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  const handleTrainModel = async () => {
    try {
      setRefreshing(true);
      const response = await apiService.trainModel();
      if (response.status === 'success') {
        // Refresh model info after training
        setTimeout(async () => {
          const modelResponse = await apiService.getModelInfo();
          if (modelResponse.status === 'success') {
            setModelInfo(modelResponse.model_info);
          }
        }, 5000);
      }
    } catch (error) {
      errorHandler.handleApiError(error, 'Failed to train model');
    } finally {
      setRefreshing(false);
    }
  };

  const handleInitializeSampleData = async () => {
    try {
      setRefreshing(true);
      const response = await apiService.initializeSampleData();
      if (response.status === 'success') {
        await loadDashboardData();
      }
    } catch (error) {
      errorHandler.handleApiError(error, 'Failed to initialize sample data');
    } finally {
      setRefreshing(false);
    }
  };

  // Prepare chart data
  const riskDistributionData = dashboardStats ? [
    { name: 'Low', value: dashboardStats.risk_distribution.Low, color: '#52c41a' },
    { name: 'Medium', value: dashboardStats.risk_distribution.Medium, color: '#faad14' },
    { name: 'High', value: dashboardStats.risk_distribution.High, color: '#fa541c' },
    { name: 'Critical', value: dashboardStats.risk_distribution.Critical, color: '#a8071a' }
  ] : [];

  const departmentData = dashboardStats ? Object.entries(dashboardStats.department_stats).map(([dept, stats]) => ({
    department: dept,
    avgRisk: stats.avg_risk.toFixed(1),
    count: stats.count,
    highRiskCount: stats.high_risk_count
  })) : [];

  // Table columns for entities
  const entityColumns = [
    {
      title: 'Entity ID',
      dataIndex: 'entity_id',
      key: 'entity_id',
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: 'Department',
      dataIndex: 'department',
      key: 'department',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
    },
    {
      title: 'Risk Score',
      dataIndex: 'current_risk_score',
      key: 'risk_score',
      render: (score) => (
        <Space>
          <Text style={{ color: riskUtils.getRiskColor(score) }}>
            {riskUtils.formatRiskScore(score)}
          </Text>
          <Tag color={riskUtils.getRiskColor(score)}>
            {riskUtils.getRiskLevel(score)}
          </Tag>
        </Space>
      ),
      sorter: (a, b) => a.current_risk_score - b.current_risk_score,
      defaultSortOrder: 'descend'
    },
    {
      title: 'Risk Level',
      dataIndex: 'current_risk_level',
      key: 'risk_level',
      render: (level) => (
        <Badge
          status={
            level === 'Critical' ? 'error' :
            level === 'High' ? 'warning' :
            level === 'Medium' ? 'processing' : 'success'
          }
          text={level}
        />
      )
    },
    {
      title: 'Recommendations',
      dataIndex: 'pending_recommendations',
      key: 'recommendations',
      render: (count) => (
        <Badge count={count} showZero style={{ backgroundColor: '#1890ff' }} />
      )
    },
    {
      title: 'Last Assessed',
      dataIndex: 'last_assessed',
      key: 'last_assessed',
      render: (date) => dataFormatter.formatDate(date)
    }
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2} style={{ margin: 0 }}>
            <ShieldOutlined style={{ marginRight: 8 }} />
            Risk Scoring Dashboard
          </Title>
        </Col>
        <Col>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={refreshing}
            >
              Refresh
            </Button>
            <Button
              type="primary"
              icon={<RobotOutlined />}
              onClick={handleTrainModel}
              loading={refreshing}
              disabled={!dashboardStats || dashboardStats.total_entities === 0}
            >
              Train Model
            </Button>
            <Button
              icon={<UserOutlined />}
              onClick={handleInitializeSampleData}
              loading={refreshing}
            >
              Initialize Sample Data
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Model Status Alert */}
      {modelInfo && (
        <Alert
          message={`Model Status: ${modelInfo.is_trained ? 'Trained' : 'Not Trained'}`}
          description={
            modelInfo.is_trained
              ? `${modelInfo.model_type} - Risk score range: ${modelInfo.risk_score_range}`
              : 'Model needs to be trained before risk assessment can be performed.'
          }
          type={modelInfo.is_trained ? 'success' : 'warning'}
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Key Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Entities"
              value={dashboardStats?.total_entities || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="High Risk Entities"
              value={dashboardStats?.high_risk_entities || 0}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#fa541c' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Average Risk Score"
              value={dashboardStats?.average_risk_score || 0}
              precision={1}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Low Risk Entities"
              value={dashboardStats?.low_risk_entities || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts Row */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* Risk Distribution Pie Chart */}
        <Col xs={24} lg={12}>
          <Card title="Risk Distribution" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={riskDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {riskDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Department Risk Analysis */}
        <Col xs={24} lg={12}>
          <Card title="Department Risk Analysis" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={departmentData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="department" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="avgRisk" fill="#1890ff" name="Avg Risk Score" />
                <Bar dataKey="highRiskCount" fill="#fa541c" name="High Risk Count" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Risk Level Progress Bars */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Risk Level Breakdown">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <Text strong>Critical Risk</Text>
                  <Progress
                    type="circle"
                    percent={dashboardStats ? Math.round((dashboardStats.risk_distribution.Critical / dashboardStats.total_entities) * 100) : 0}
                    strokeColor="#a8071a"
                    format={percent => `${dashboardStats?.risk_distribution.Critical || 0}`}
                  />
                </div>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <Text strong>High Risk</Text>
                  <Progress
                    type="circle"
                    percent={dashboardStats ? Math.round((dashboardStats.risk_distribution.High / dashboardStats.total_entities) * 100) : 0}
                    strokeColor="#fa541c"
                    format={percent => `${dashboardStats?.risk_distribution.High || 0}`}
                  />
                </div>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <Text strong>Medium Risk</Text>
                  <Progress
                    type="circle"
                    percent={dashboardStats ? Math.round((dashboardStats.risk_distribution.Medium / dashboardStats.total_entities) * 100) : 0}
                    strokeColor="#faad14"
                    format={percent => `${dashboardStats?.risk_distribution.Medium || 0}`}
                  />
                </div>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <Text strong>Low Risk</Text>
                  <Progress
                    type="circle"
                    percent={dashboardStats ? Math.round((dashboardStats.risk_distribution.Low / dashboardStats.total_entities) * 100) : 0}
                    strokeColor="#52c41a"
                    format={percent => `${dashboardStats?.risk_distribution.Low || 0}`}
                  />
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Entities Table */}
      <Row>
        <Col span={24}>
          <Card 
            title="Entity Risk Scores" 
            extra={
              <Space>
                <Text type="secondary">
                  Showing {entities.length} entities
                </Text>
              </Space>
            }
          >
            <Table
              dataSource={entities}
              columns={entityColumns}
              rowKey="entity_id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} of ${total} entities`
              }}
              scroll={{ x: 800 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;