import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Space,
  Row,
  Col,
  Typography,
  Tag,
  Popconfirm,
  Alert,
  Divider
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  ShieldOutlined
} from '@ant-design/icons';
import { apiService, errorHandler, dataFormatter } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const SecurityRules = () => {
  const [loading, setLoading] = useState(false);
  const [rules, setRules] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadSecurityRules();
  }, []);

  const loadSecurityRules = async () => {
    try {
      setLoading(true);
      const response = await apiService.getSecurityRules();
      if (response.status === 'success') {
        setRules(response.rules);
      }
    } catch (error) {
      errorHandler.handleApiError(error, 'Failed to load security rules');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRule = () => {
    setEditingRule(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEditRule = (rule) => {
    setEditingRule(rule);
    form.setFieldsValue({
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      weight: rule.weight,
      enabled: rule.enabled
    });
    setModalVisible(true);
  };

  const handleSaveRule = async (values) => {
    try {
      const ruleData = {
        rule_id: editingRule?.rule_id || `rule_${Date.now()}`,
        rule_name: values.rule_name,
        rule_type: values.rule_type,
        conditions: [
          {
            field: values.condition_field,
            operator: values.condition_operator,
            value: values.condition_value
          }
        ],
        weight: values.weight,
        enabled: values.enabled
      };

      const response = await apiService.createSecurityRule(ruleData);
      if (response.status === 'success') {
        setModalVisible(false);
        loadSecurityRules();
        form.resetFields();
      }
    } catch (error) {
      errorHandler.handleApiError(error, 'Failed to save security rule');
    }
  };

  const predefinedRuleTemplates = [
    {
      name: 'High Login Failures',
      type: 'authentication',
      field: 'failed_logins',
      operator: 'gt',
      value: 5,
      weight: 2.0
    },
    {
      name: 'Excessive Data Access',
      type: 'data_access',
      field: 'data_accessed_gb',
      operator: 'gt',
      value: 100,
      weight: 1.5
    },
    {
      name: 'After Hours Activity',
      type: 'schedule',
      field: 'after_hours_activity',
      operator: 'gt',
      value: 20,
      weight: 1.8
    },
    {
      name: 'Privilege Escalation',
      type: 'access_control',
      field: 'privilege_escalations',
      operator: 'gt',
      value: 2,
      weight: 3.0
    },
    {
      name: 'Suspicious File Access',
      type: 'file_access',
      field: 'suspicious_file_access',
      operator: 'gt',
      value: 10,
      weight: 2.5
    },
    {
      name: 'Network Anomalies',
      type: 'network',
      field: 'network_anomalies',
      operator: 'gt',
      value: 15,
      weight: 2.0
    }
  ];

  const handleUseTemplate = (template) => {
    form.setFieldsValue({
      rule_name: template.name,
      rule_type: template.type,
      condition_field: template.field,
      condition_operator: template.operator,
      condition_value: template.value,
      weight: template.weight,
      enabled: true
    });
  };

  const columns = [
    {
      title: 'Rule Name',
      dataIndex: 'rule_name',
      key: 'rule_name',
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: 'Type',
      dataIndex: 'rule_type',
      key: 'rule_type',
      render: (type) => <Tag color="blue">{type}</Tag>
    },
    {
      title: 'Conditions',
      dataIndex: 'conditions',
      key: 'conditions',
      render: (conditions) => (
        <div>
          {conditions?.map((condition, index) => (
            <Tag key={index} style={{ marginBottom: 4 }}>
              {condition.field} {condition.operator} {condition.value}
            </Tag>
          ))}
        </div>
      )
    },
    {
      title: 'Weight',
      dataIndex: 'weight',
      key: 'weight',
      render: (weight) => (
        <Tag color={weight > 2 ? 'red' : weight > 1 ? 'orange' : 'green'}>
          {weight}
        </Tag>
      )
    },
    {
      title: 'Status',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled) => (
        <Tag color={enabled ? 'green' : 'red'}>
          {enabled ? 'Enabled' : 'Disabled'}
        </Tag>
      )
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => dataFormatter.formatDate(date)
    },
    {
      title: 'Triggered',
      dataIndex: 'trigger_count',
      key: 'trigger_count',
      render: (count) => <Text>{count || 0}</Text>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEditRule(record)}
          >
            Edit
          </Button>
          <Popconfirm
            title="Are you sure you want to delete this rule?"
            onConfirm={() => handleDeleteRule(record.rule_id)}
          >
            <Button
              icon={<DeleteOutlined />}
              size="small"
              danger
            >
              Delete
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  const handleDeleteRule = async (ruleId) => {
    // This would need to be implemented in the backend
    console.log('Delete rule:', ruleId);
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>
            <ShieldOutlined /> Security Rules Management
          </Title>
          <Text type="secondary">
            Define and manage security rules for pattern detection and risk assessment.
          </Text>
        </Col>
        <Col>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreateRule}
            >
              Create Rule
            </Button>
            <Button
              icon={<PlayCircleOutlined />}
              onClick={() => apiService.detectPatterns()}
            >
              Test Rules
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Rules Table */}
      <Card title="Security Rules">
        <Table
          dataSource={rules}
          columns={columns}
          rowKey="rule_id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true
          }}
        />
      </Card>

      {/* Create/Edit Rule Modal */}
      <Modal
        title={editingRule ? 'Edit Security Rule' : 'Create Security Rule'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveRule}
          initialValues={{
            enabled: true,
            weight: 1.0,
            condition_operator: 'gt'
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="rule_name"
                label="Rule Name"
                rules={[{ required: true, message: 'Please enter rule name' }]}
              >
                <Input placeholder="Enter rule name" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="rule_type"
                label="Rule Type"
                rules={[{ required: true, message: 'Please select rule type' }]}
              >
                <Select placeholder="Select rule type">
                  <Option value="authentication">Authentication</Option>
                  <Option value="data_access">Data Access</Option>
                  <Option value="schedule">Schedule</Option>
                  <Option value="access_control">Access Control</Option>
                  <Option value="file_access">File Access</Option>
                  <Option value="network">Network</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider>Condition</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="condition_field"
                label="Field"
                rules={[{ required: true, message: 'Please select field' }]}
              >
                <Select placeholder="Select field">
                  <Option value="failed_logins">Failed Logins</Option>
                  <Option value="data_accessed_gb">Data Accessed (GB)</Option>
                  <Option value="after_hours_activity">After Hours Activity</Option>
                  <Option value="privilege_escalations">Privilege Escalations</Option>
                  <Option value="suspicious_file_access">Suspicious File Access</Option>
                  <Option value="network_anomalies">Network Anomalies</Option>
                  <Option value="login_attempts">Login Attempts</Option>
                  <Option value="vpn_connections">VPN Connections</Option>
                  <Option value="admin_commands">Admin Commands</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="condition_operator"
                label="Operator"
                rules={[{ required: true, message: 'Please select operator' }]}
              >
                <Select>
                  <Option value="gt">Greater Than (&gt;)</Option>
                  <Option value="lt">Less Than (&lt;)</Option>
                  <Option value="eq">Equal To (=)</Option>
                  <Option value="contains">Contains</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="condition_value"
                label="Value"
                rules={[{ required: true, message: 'Please enter value' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="Enter threshold value"
                  min={0}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="weight"
                label="Weight"
                rules={[{ required: true, message: 'Please enter weight' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="Rule weight (1.0 - 5.0)"
                  min={0.1}
                  max={5.0}
                  step={0.1}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="enabled"
                label="Enabled"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Quick Templates</Divider>
          
          <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
            {predefinedRuleTemplates.map((template, index) => (
              <Col key={index}>
                <Button
                  size="small"
                  onClick={() => handleUseTemplate(template)}
                >
                  {template.name}
                </Button>
              </Col>
            ))}
          </Row>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {editingRule ? 'Update Rule' : 'Create Rule'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SecurityRules;