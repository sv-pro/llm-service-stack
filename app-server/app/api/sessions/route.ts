import { NextRequest, NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import { Session, Message } from '@/lib/models';

/**
 * Chat session management API endpoints
 * Handles creating, listing, and managing chat sessions
 */

export async function GET(request: NextRequest) {
  try {
    await connectDB();

    const { searchParams } = new URL(request.url);
    const sessionId = searchParams.get('id');
    const userId = searchParams.get('userId');

    if (sessionId) {
      // Get specific session with messages
      const session = await Session.findById(sessionId).select('-__v');

      if (!session) {
        return NextResponse.json(
          { error: 'Session not found' },
          { status: 404 }
        );
      }

      // Get messages for this session
      const messages = await Message.find({ sessionId })
        .select('-__v')
        .sort({ createdAt: 1 });

      return NextResponse.json({
        session,
        messages,
      });
    } else if (userId) {
      // Get all sessions for a user
      const page = parseInt(searchParams.get('page') || '1');
      const limit = parseInt(searchParams.get('limit') || '20');
      const skip = (page - 1) * limit;

      const [sessions, total] = await Promise.all([
        Session.find({ userId })
          .select('-__v')
          .skip(skip)
          .limit(limit)
          .sort({ updatedAt: -1 }),
        Session.countDocuments({ userId }),
      ]);

      return NextResponse.json({
        sessions,
        pagination: {
          page,
          limit,
          total,
          pages: Math.ceil(total / limit),
        },
      });
    } else {
      return NextResponse.json(
        { error: 'Either sessionId or userId is required' },
        { status: 400 }
      );
    }
  } catch (error) {
    console.error('Error fetching sessions:', error);
    return NextResponse.json(
      { error: 'Failed to fetch sessions' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    await connectDB();

    const body = await request.json();
    const { userId, title, model, metadata } = body;

    // Validate input
    if (!userId) {
      return NextResponse.json(
        { error: 'userId is required' },
        { status: 400 }
      );
    }

    // Create new session
    const session = await Session.create({
      userId,
      title,
      llmModel: model || 'gpt-3.5-turbo',
      metadata,
    });

    return NextResponse.json(
      {
        message: 'Session created successfully',
        session: {
          id: session._id,
          userId: session.userId,
          title: session.title,
          model: session.llmModel,
          metadata: session.metadata,
          createdAt: session.createdAt,
          updatedAt: session.updatedAt,
        }
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Error creating session:', error);
    return NextResponse.json(
      { error: 'Failed to create session' },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    await connectDB();

    const body = await request.json();
    const { id, title, model, metadata } = body;

    if (!id) {
      return NextResponse.json(
        { error: 'Session ID is required' },
        { status: 400 }
      );
    }

    // Prepare update data
    const updateData: any = {};
    if (title !== undefined) updateData.title = title;
    if (model) updateData.llmModel = model;
    if (metadata !== undefined) updateData.metadata = metadata;

    // Update session
    const session = await Session.findByIdAndUpdate(
      id,
      updateData,
      { new: true, runValidators: true }
    ).select('-__v');

    if (!session) {
      return NextResponse.json(
        { error: 'Session not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      message: 'Session updated successfully',
      session: {
        ...session.toObject(),
        model: session.llmModel, // Map llmModel back to model for API consistency
      },
    });
  } catch (error) {
    console.error('Error updating session:', error);
    return NextResponse.json(
      { error: 'Failed to update session' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    await connectDB();

    const { searchParams } = new URL(request.url);
    const sessionId = searchParams.get('id');

    if (!sessionId) {
      return NextResponse.json(
        { error: 'Session ID is required' },
        { status: 400 }
      );
    }

    // Delete session and all associated messages
    const [session, deletedMessages] = await Promise.all([
      Session.findByIdAndDelete(sessionId),
      Message.deleteMany({ sessionId }),
    ]);

    if (!session) {
      return NextResponse.json(
        { error: 'Session not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      message: 'Session deleted successfully',
      sessionId,
      deletedMessages: deletedMessages.deletedCount,
    });
  } catch (error) {
    console.error('Error deleting session:', error);
    return NextResponse.json(
      { error: 'Failed to delete session' },
      { status: 500 }
    );
  }
}
