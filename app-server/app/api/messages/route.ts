import { NextRequest, NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import { Message } from '@/lib/models';

/**
 * Message management API endpoints
 * Handles creating and retrieving messages within sessions
 */

export async function GET(request: NextRequest) {
  try {
    await connectDB();

    const { searchParams } = new URL(request.url);
    const sessionId = searchParams.get('sessionId');
    const messageId = searchParams.get('id');

    if (messageId) {
      // Get specific message
      const message = await Message.findById(messageId).select('-__v');

      if (!message) {
        return NextResponse.json(
          { error: 'Message not found' },
          { status: 404 }
        );
      }

      return NextResponse.json({ message });
    } else if (sessionId) {
      // Get all messages for a session
      const messages = await Message.find({ sessionId })
        .select('-__v')
        .sort({ createdAt: 1 });

      return NextResponse.json({
        messages,
        count: messages.length,
      });
    } else {
      return NextResponse.json(
        { error: 'Either sessionId or id is required' },
        { status: 400 }
      );
    }
  } catch (error) {
    console.error('Error fetching messages:', error);
    return NextResponse.json(
      { error: 'Failed to fetch messages' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    await connectDB();

    const body = await request.json();
    const { sessionId, role, content, tokens, cost } = body;

    // Validate input
    if (!sessionId) {
      return NextResponse.json(
        { error: 'sessionId is required' },
        { status: 400 }
      );
    }

    if (!role || !content) {
      return NextResponse.json(
        { error: 'role and content are required' },
        { status: 400 }
      );
    }

    if (!['user', 'assistant', 'system'].includes(role)) {
      return NextResponse.json(
        { error: 'role must be user, assistant, or system' },
        { status: 400 }
      );
    }

    // Create new message
    const message = await Message.create({
      sessionId,
      role,
      content,
      tokens,
      cost,
      createdAt: new Date(),
    });

    return NextResponse.json(
      {
        message: 'Message created successfully',
        data: {
          id: message._id,
          sessionId: message.sessionId,
          role: message.role,
          content: message.content,
          tokens: message.tokens,
          cost: message.cost,
          createdAt: message.createdAt,
        }
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Error creating message:', error);
    return NextResponse.json(
      { error: 'Failed to create message' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    await connectDB();

    const { searchParams } = new URL(request.url);
    const messageId = searchParams.get('id');

    if (!messageId) {
      return NextResponse.json(
        { error: 'Message ID is required' },
        { status: 400 }
      );
    }

    const message = await Message.findByIdAndDelete(messageId);

    if (!message) {
      return NextResponse.json(
        { error: 'Message not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      message: 'Message deleted successfully',
      messageId,
    });
  } catch (error) {
    console.error('Error deleting message:', error);
    return NextResponse.json(
      { error: 'Failed to delete message' },
      { status: 500 }
    );
  }
}
