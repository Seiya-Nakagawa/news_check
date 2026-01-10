import '@testing-library/jest-dom'
import { render, screen, waitFor } from '@testing-library/react'
import Home from '../src/app/page'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useSearchParams: () => ({
    get: jest.fn().mockReturnValue(null),
  }),
  useRouter: () => ({
    push: jest.fn(),
  }),
}))

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve([
      {
        youtube_id: 'vid1',
        title: 'Test Video 1',
        summary: 'Summary 1',
        published_at: '2024-01-01T10:00:00Z',
        status: 'processed',
        key_points: [{ point: 'Point 1' }]
      },
      {
        youtube_id: 'vid2',
        title: 'Test Video 2',
        summary: 'Summary 2',
        published_at: '2024-01-02T10:00:00Z',
        status: 'processed',
        key_points: [{ point: 'Point 2' }]
      }
    ]),
  })
) as jest.Mock;

describe('Home Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(<Home />)
    expect(screen.getByText('ニュースを読み込んでいます...')).toBeInTheDocument()
  })

  it('renders news items after fetch', async () => {
    // 非同期処理が含まれるため waitFor を使用
    // act警告が出るかもしれないが一旦無視
    const jsx = await Home()
    // Home コンポーネントは async function ではないが、Suspenseを使っている
    // 今回の構成では Home はコンポーネントとしてレンダリングする

    render(<Home />)

    await waitFor(() => {
        // ローディングが消えていること
        const loader = screen.queryByText('ニュースを読み込んでいます...')
        expect(loader).not.toBeInTheDocument()
    })

    expect(screen.getByText('Test Video 1')).toBeInTheDocument()
    expect(screen.getByText('Test Video 2')).toBeInTheDocument()
  })
})
