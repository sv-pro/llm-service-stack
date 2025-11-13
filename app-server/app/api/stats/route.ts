import { NextRequest, NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import { User, Session, Message, ApiKey } from '@/lib/models';

/**
 * Stats API endpoint
 * Provides aggregated statistics for the dashboard
 */

export async function GET(request: NextRequest) {
  try {
    await connectDB();

    // Get counts from all collections
    const [
      totalUsers,
      totalSessions,
      totalApiKeys,
      activeApiKeys,
      totalMessages,
    ] = await Promise.all([
      User.countDocuments(),
      Session.countDocuments(),
      ApiKey.countDocuments(),
      ApiKey.countDocuments({ isActive: true }),
      Message.countDocuments(),
    ]);

    // Get recent activity (last 10 items)
    const recentUsers = await User.find()
      .sort({ createdAt: -1 })
      .limit(10)
      .select('email name createdAt');

    const recentSessions = await Session.find()
      .sort({ createdAt: -1 })
      .limit(10)
      .select('title llmModel userId createdAt')
      .populate('userId', 'email name');

    const recentApiKeys = await ApiKey.find()
      .sort({ createdAt: -1 })
      .limit(10)
      .select('name keyPrefix userId createdAt lastUsedAt')
      .populate('userId', 'email name');

    // Calculate messages per session (top sessions by message count)
    const messageCounts = await Message.aggregate([
      {
        $group: {
          _id: '$sessionId',
          count: { $sum: 1 }
        }
      },
      { $sort: { count: -1 } },
      { $limit: 10 }
    ]);

    return NextResponse.json({
      stats: {
        totalUsers,
        totalSessions,
        totalApiKeys,
        activeApiKeys,
        totalMessages,
      },
      recentActivity: {
        users: recentUsers,
        sessions: recentSessions,
        apiKeys: recentApiKeys,
      },
      topSessions: messageCounts,
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    return NextResponse.json(
      { error: 'Failed to fetch stats' },
      { status: 500 }
    );
  }
}
