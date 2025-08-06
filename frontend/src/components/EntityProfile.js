import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Table,
  Button,
  Space,
  Row,
  Col,
  Typography,
  Spin,
  Tag,
  Statistic,
  List,
  Timeline,
  Alert
} from 'antd';
import {
  UserOutlined,
  WarningOutlined,
  TrendingUpOutlined,
  TrendingDownOutlined,
  MinusOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService, riskUtils, errorHandler, dataFormatter } from '../services/api';

const { Title, Text } = Typography;

const EntityProfile = () => {
  const { entityId } = useParams();
  const [selectedEntityId, setSelectedEntityId] = useState(entityId);
  const [loading, setLoading] = useState(false);
  const [entities, setEntities] = useState([]);
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    loadEntities();
  }, []);

  useEffect(() => {
    if (selectedEntityId) {
      loadEntityProfile(selectedEntityId);
    }
  }, [selectedEntityId]);

  const loadEntities = async () => {
    try {
      const response = await apiService.getEntities();
      if (response.status === 'success') {
        setEntities(response.entities);
        if (!selectedEntityId && response.entities.length > 0) {
          setSelectedEntityId(response.entities[0].entity_id);
        }
      }
    } catch (error) {
      errorHandler.handleApiError(error, 'Failed to load entities');
    }
  };

  const loadEntityProfile = async (entityId) => {
    try {
      setLoading(true);
      const response = await apiService.getEntityProfile(entityId);
      if (response.status === 'success') {
        setProfile(response.profile);
      }
    } catch (error) {
      errorHandler.handleApiError(error, 'Failed to load entity profile');
    } finally {
      setLoading(false);
    }
  };

  const handleImplementRecommendation = async (recommendationId) => {
    try {
      const response = await apiService.implementRecommendation(recommendationId);
      if (response.status === 'success') {
        // Reload profile to update recommendations
        loadEntityProfile(selectedEntityId);
      }
    } catch (error) {
      errorHandler.handleApiError(error, 'Failed to implement recommendation');
    }
  };

  const riskHistoryColumns = [
    {
      title: 'Date',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => dataFormatter.formatDate(timestamp)
    },
    {
      title: 'Risk Score',
      dataIndex: 'risk_score',
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
      )
    },
    {
      title: 'Risk Level',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level) => <Tag>{level}</Tag>
    }
  ];

  const recommendationsColumns = [
    {
      title: 'Type',
      dataIndex: 'recommendation_type',
      key: 'type',
      render: (type) => <Tag color="blue">{type}</Tag>
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority) => (
        <Tag color={priority > 7 ? 'red' : priority > 5 ? 'orange' : 'green'}>
          {priority}/10
        </Tag>
      )
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created',
      render: (date) => dataFormatter.formatDate(date)
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Button
          size="small"
          type="primary"
          onClick={() => handleImplementRecommendation(record.id)}
        >
          Implement
        </Button>
      )
    }
  ];

  if (loading && !profile) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Loading entity profile...</div>
      </div>
    );
  }

  if (!selectedEntityId) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="No Entity Selected"
          description="Please select an entity to view its profile."
          type="info"
          showIcon
        />
      </div>
    );
  }

  const entityInfo = profile?.entity_info;
  const riskStats = profile?.risk_statistics;
  const trendIcon = profile?.risk_trend === 'increasing' ? <TrendingUpOutlined style={{ color: '#fa541c' }} /> :
                   profile?.risk_trend === 'decreasing' ? <TrendingDownOutlined style={{ color: '#52c41a' }} /> :
                   <MinusOutlined style={{ color: '#1890ff' }} />;

  // Prepare chart data
  const chartData = profile?.risk_history?.slice(0, 30).reverse().map(item => ({
    date: new Date(item.timestamp).toLocaleDateString(),
    risk_score: item.risk_score
  })) || [];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>
            <UserOutlined /> Entity Profile
          </Title>
        </Col>
        <Col>
          <Space>
            <Button onClick={() => loadEntityProfile(selectedEntityId)}>
              Refresh
            </Button>
          </Space>
        </Col>
      </Row>

      {profile && (
        <div>
          {/* Entity Basic Information */}
          <Card title="Entity Information" style={{ marginBottom: 24 }}>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="Entity ID">{entityInfo?.entity_id}</Descriptions.Item>
              <Descriptions.Item label="Type">{entityInfo?.entity_type}</Descriptions.Item>
              <Descriptions.Item label="Department">{entityInfo?.department}</Descriptions.Item>
              <Descriptions.Item label="Role">{entityInfo?.role}</Descriptions.Item>
              <Descriptions.Item label="Access Level">{entityInfo?.access_level}</Descriptions.Item>
              <Descriptions.Item label="Status">{entityInfo?.status}</Descriptions.Item>
              <Descriptions.Item label="Created">{dataFormatter.formatDate(entityInfo?.created_at)}</Descriptions.Item>
              <Descriptions.Item label="Last Updated">{dataFormatter.formatDate(entityInfo?.last_updated)}</Descriptions.Item>
            </Descriptions>
          </Card>

          {/* Current Risk Status */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Current Risk Score"
                  value={profile.current_risk_score}
                  precision={1}
                  valueStyle={{ color: riskUtils.getRiskColor(profile.current_risk_score) }}
                  prefix={<WarningOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Risk Level"
                  value={profile.current_risk_level}
                  valueStyle={{ color: riskUtils.getRiskColor(profile.current_risk_score) }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Risk Trend"
                  value={profile.risk_trend}
                  prefix={trendIcon}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Active Recommendations"
                  value={profile.active_recommendations?.length || 0}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Risk Statistics */}
          {riskStats && (
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="Average Risk"
                    value={riskStats.average_score}
                    precision={1}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="Maximum Risk"
                    value={riskStats.max_score}
                    precision={1}
                    valueStyle={{ color: '#fa541c' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="High Risk Incidents"
                    value={riskStats.high_risk_incidents}
                    valueStyle={{ color: '#fa541c' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="Days Tracked"
                    value={riskStats.days_tracked}
                  />
                </Card>
              </Col>
            </Row>
          )}

          {/* Risk Trend Chart */}
          <Card title="Risk Score History" style={{ marginBottom: 24 }}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[0, 50]} />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="risk_score" 
                  stroke={riskUtils.getRiskColor(profile.current_risk_score)}
                  strokeWidth={2}
                  dot={{ fill: riskUtils.getRiskColor(profile.current_risk_score) }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Active Recommendations */}
          {profile.active_recommendations && profile.active_recommendations.length > 0 && (
            <Card title="Active Recommendations" style={{ marginBottom: 24 }}>
              <Table
                dataSource={profile.active_recommendations}
                columns={recommendationsColumns}
                rowKey="id"
                pagination={false}
                size="small"
              />
            </Card>
          )}

          {/* Risk History Table */}
          <Card title="Recent Risk History">
            <Table
              dataSource={profile.risk_history?.slice(0, 20) || []}
              columns={riskHistoryColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </Card>
        </div>
      )}
    </div>
  );
};

export default EntityProfile;