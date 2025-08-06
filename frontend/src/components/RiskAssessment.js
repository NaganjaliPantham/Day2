import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Table,
  Select,
  Space,
  Row,
  Col,
  Typography,
  Alert,
  Spin,
  Progress,
  Tag,
  Divider,
  List,
  Collapse,
  Statistic
} from 'antd';
import {
  PlayCircleOutlined,
  ReloadOutlined,
  DownloadOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService, riskUtils, errorHandler, dataFormatter } from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { Panel } = Collapse;

const RiskAssessment = () => {
  const [loading, setLoading] = useState(false);
  const [entities, setEntities] = useState([]);
  const [selectedEntityIds, setSelectedEntityIds] = useState([]);
  const [assessmentResults, setAssessmentResults] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [patternResults, setPatternResults] = useState(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [entitiesResponse, modelResponse] = await Promise.all([
        apiService.getEntities(),
        apiService.getModelInfo()
      ]);

      if (entitiesResponse.status === 'success') {
        setEntities(entitiesResponse.entities);
        // Pre-select high-risk entities
        const highRiskEntities = entitiesResponse.entities
          .filter(e => e.current_risk_score > 20)
          .map(e => e.entity_id)
          .slice(0, 10); // Limit to 10 for performance
        setSelectedEntityIds(highRiskEntities);
      }

      if (modelResponse.status === 'success') {
        setModelInfo(modelResponse.model_info);
      }
    } catch (error) {
      errorHandler.handleApiError(error, 'Failed to load assessment data');
    } finally {
      setLoading(false);
    }
  };

  const handleRunAssessment = async () => {
    if (selectedEntityIds.length === 0) {
      errorHandler.handleApiError({ message: 'Please select at least one entity' });
      return;
    }

    try {
      setLoading(true);
      
      // Run risk assessment
      const assessmentResponse = await apiService.assessRisk(selectedEntityIds, true);
      
      if (assessmentResponse.status === 'success') {
        setAssessmentResults(assessmentResponse);
      }

      // Run pattern detection
      const patternResponse = await apiService.detectPatterns();
      if (patternResponse.status === 'success') {
        setPatternResults(patternResponse);
      }

    } catch (error) {
      errorHandler.handleApiError(error, 'Risk assessment failed');
    } finally {
      setLoading(false);
    }
  };

  const handleEntitySelection = (values) => {
    setSelectedEntityIds(values);
  };

  const riskColumns = [
    {
      title: 'Entity ID',
      dataIndex: 'entity_id',
      key: 'entity_id',
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: 'Risk Score',
      dataIndex: 'risk_score',
      key: 'risk_score',
      render: (score) => (
        <Space>
          <Text style={{ color: riskUtils.getRiskColor(score), fontSize: 16, fontWeight: 'bold' }}>
            {riskUtils.formatRiskScore(score)}
          </Text>
          <Progress
            percent={(score / 50) * 100}
            strokeColor={riskUtils.getRiskColor(score)}
            showInfo={false}
            size="small"
            style={{ width: 60 }}
          />
        </Space>
      ),
      sorter: (a, b) => a.risk_score - b.risk_score,
      defaultSortOrder: 'descend'
    },
    {
      title: 'Risk Level',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level, record) => (
        <Tag color={riskUtils.getRiskColor(record.risk_score)}>
          {level}
        </Tag>
      )
    },
    {
      title: 'Is Anomaly',
      dataIndex: 'is_anomaly',
      key: 'is_anomaly',
      render: (isAnomaly) => (
        isAnomaly ? 
          <Tag color="red"><WarningOutlined /> Yes</Tag> : 
          <Tag color="green"><CheckCircleOutlined /> No</Tag>
      )
    },
    {
      title: 'Anomaly Score',
      dataIndex: 'anomaly_score',
      key: 'anomaly_score',
      render: (score) => dataFormatter.formatNumber(score, 3)
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => dataFormatter.formatDate(timestamp)
    }
  ];

  const contributingFactorsColumns = [
    {
      title: 'Feature',
      dataIndex: 'feature',
      key: 'feature',
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      render: (value) => dataFormatter.formatNumber(value, 2)
    },
    {
      title: 'Importance',
      dataIndex: 'importance',
      key: 'importance',
      render: (importance) => (
        <Space>
          <Progress
            percent={importance * 100}
            strokeColor="#1890ff"
            size="small"
            style={{ width: 100 }}
          />
          <Text>{(importance * 100).toFixed(1)}%</Text>
        </Space>
      )
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description'
    }
  ];

  const recommendationColumns = [
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category) => <Tag color="blue">{category}</Tag>
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
      ),
      sorter: (a, b) => a.priority - b.priority,
      defaultSortOrder: 'descend'
    },
    {
      title: 'Expected Impact',
      dataIndex: 'expected_impact',
      key: 'expected_impact',
      render: (impact) => (
        <Progress
          percent={impact * 100}
          strokeColor="#52c41a"
          size="small"
          style={{ width: 80 }}
        />
      )
    },
    {
      title: 'Effort',
      dataIndex: 'estimated_effort',
      key: 'effort',
      render: (effort) => <Tag color={effort === 'High' ? 'red' : effort === 'Medium' ? 'orange' : 'green'}>{effort}</Tag>
    }
  ];

  if (loading && !assessmentResults) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Loading risk assessment...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>Risk Assessment</Title>
          <Paragraph>
            Perform comprehensive risk analysis on selected entities using machine learning models.
          </Paragraph>
        </Col>
      </Row>

      {/* Model Status */}
      {modelInfo && (
        <Alert
          message={`Model Status: ${modelInfo.is_trained ? 'Ready' : 'Not Trained'}`}
          description={
            modelInfo.is_trained
              ? `Model is trained and ready for assessment. Type: ${modelInfo.model_type}`
              : 'Model needs to be trained before running assessments. Please go to Dashboard to train the model.'
          }
          type={modelInfo.is_trained ? 'success' : 'error'}
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Assessment Controls */}
      <Card title="Assessment Configuration" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col span={18}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>Select Entities for Assessment:</Text>
            </div>
            <Select
              mode="multiple"
              style={{ width: '100%' }}
              placeholder="Select entities to assess"
              value={selectedEntityIds}
              onChange={handleEntitySelection}
              showSearch
              filterOption={(input, option) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
            >
              {entities.map(entity => (
                <Option key={entity.entity_id} value={entity.entity_id}>
                  {entity.entity_id} - {entity.department} ({entity.role})
                </Option>
              ))}
            </Select>
            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>
              Selected: {selectedEntityIds.length} entities
            </Text>
          </Col>
          <Col span={6}>
            <Space>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleRunAssessment}
                loading={loading}
                disabled={!modelInfo?.is_trained || selectedEntityIds.length === 0}
                size="large"
              >
                Run Assessment
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={loadInitialData}
                loading={loading}
              >
                Refresh
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Assessment Results */}
      {assessmentResults && (
        <div>
          {/* Summary Statistics */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Entities Assessed"
                  value={assessmentResults.predictions?.length || 0}
                  prefix={<InfoCircleOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="High Risk Detected"
                  value={assessmentResults.predictions?.filter(p => p.risk_score > 30).length || 0}
                  prefix={<WarningOutlined />}
                  valueStyle={{ color: '#fa541c' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Anomalies Found"
                  value={assessmentResults.predictions?.filter(p => p.is_anomaly).length || 0}
                  prefix={<WarningOutlined />}
                  valueStyle={{ color: '#a8071a' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Model Confidence"
                  value={assessmentResults.model_confidence || 0}
                  precision={3}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Risk Assessment Results Table */}
          <Card 
            title="Risk Assessment Results" 
            style={{ marginBottom: 24 }}
            extra={
              <Button icon={<DownloadOutlined />} type="link">
                Export Results
              </Button>
            }
          >
            <Table
              dataSource={assessmentResults.predictions}
              columns={riskColumns}
              rowKey="entity_id"
              pagination={{ pageSize: 10 }}
              expandable={{
                expandedRowRender: (record) => (
                  <div style={{ padding: 16 }}>
                    <Title level={5}>Contributing Factors</Title>
                    <Table
                      dataSource={record.contributing_factors}
                      columns={contributingFactorsColumns}
                      pagination={false}
                      size="small"
                      style={{ marginBottom: 16 }}
                    />
                    
                    {record.custom_recommendations && record.custom_recommendations.length > 0 && (
                      <div>
                        <Title level={5}>Recommendations</Title>
                        <Table
                          dataSource={record.custom_recommendations}
                          columns={recommendationColumns}
                          pagination={false}
                          size="small"
                        />
                      </div>
                    )}
                  </div>
                ),
                rowExpandable: (record) => record.contributing_factors && record.contributing_factors.length > 0,
              }}
            />
          </Card>

          {/* Pattern Detection Results */}
          {patternResults && patternResults.detected_patterns && patternResults.detected_patterns.length > 0 && (
            <Card title="Pattern Detection Results" style={{ marginBottom: 24 }}>
              <Alert
                message={`${patternResults.total_patterns} suspicious patterns detected`}
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
              
              <List
                dataSource={patternResults.detected_patterns}
                renderItem={(pattern) => (
                  <List.Item>
                    <Card size="small" style={{ width: '100%' }}>
                      <Row justify="space-between">
                        <Col span={18}>
                          <Space direction="vertical" size="small">
                            <Text strong>Entity: {pattern.entity_id}</Text>
                            <Text>Pattern: {pattern.pattern_id}</Text>
                            <Text type="secondary">Weight: {pattern.weight}</Text>
                            <Text type="secondary">Time: {dataFormatter.formatDate(pattern.timestamp)}</Text>
                          </Space>
                        </Col>
                        <Col span={6} style={{ textAlign: 'right' }}>
                          <Tag color={pattern.weight > 2 ? 'red' : pattern.weight > 1 ? 'orange' : 'blue'}>
                            Weight: {pattern.weight}
                          </Tag>
                        </Col>
                      </Row>
                      
                      {pattern.details && (
                        <Collapse size="small" style={{ marginTop: 12 }}>
                          <Panel header="Pattern Details" key="1">
                            <Text>{pattern.details.rule_description}</Text>
                            {pattern.details.triggered_conditions && (
                              <div style={{ marginTop: 8 }}>
                                <Text strong>Triggered Conditions:</Text>
                                <ul>
                                  {pattern.details.triggered_conditions.map((condition, idx) => (
                                    <li key={idx}>
                                      {condition.field} {condition.operator} {condition.threshold} 
                                      (actual: {condition.actual_value})
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </Panel>
                        </Collapse>
                      )}
                    </Card>
                  </List.Item>
                )}
              />
            </Card>
          )}
        </div>
      )}

      {/* Empty State */}
      {!assessmentResults && !loading && (
        <Card style={{ textAlign: 'center', padding: '50px' }}>
          <PlayCircleOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
          <Title level={4} type="secondary">No Assessment Results</Title>
          <Paragraph type="secondary">
            Select entities and click "Run Assessment" to perform risk analysis.
          </Paragraph>
        </Card>
      )}
    </div>
  );
};

export default RiskAssessment;