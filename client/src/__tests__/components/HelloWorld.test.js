// ============================================================================
// HelloWorld.vue 组件单元测试
// ============================================================================

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import HelloWorld from '../../components/HelloWorld.vue'

describe('HelloWorld.vue', () => {
  it('渲染组件 — 包含 "Get started" 标题', () => {
    const wrapper = mount(HelloWorld)
    expect(wrapper.text()).toContain('Get started')
  })

  it('渲染组件 — 包含计数按钮', () => {
    const wrapper = mount(HelloWorld)
    expect(wrapper.find('button.counter').exists()).toBe(true)
    expect(wrapper.text()).toContain('Count is 0')
  })

  it('点击按钮时计数增加', async () => {
    const wrapper = mount(HelloWorld)
    const button = wrapper.find('button.counter')

    // 初始计数为 0
    expect(wrapper.text()).toContain('Count is 0')

    // 点击一次
    await button.trigger('click')
    expect(wrapper.text()).toContain('Count is 1')

    // 再点击两次
    await button.trigger('click')
    await button.trigger('click')
    expect(wrapper.text()).toContain('Count is 3')
  })

  it('渲染所有文档链接', () => {
    const wrapper = mount(HelloWorld)
    const links = wrapper.findAll('a')
    expect(links.length).toBeGreaterThanOrEqual(2)
    expect(wrapper.text()).toContain('Explore Vite')
    expect(wrapper.text()).toContain('Learn more')
  })
})
